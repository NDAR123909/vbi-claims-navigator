"""RAG (Retrieval-Augmented Generation) service."""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.services.llm import llm_service


class RAGService:
    """Service for RAG operations with vector database."""

    def __init__(self):
        """Initialize RAG service with Qdrant client."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the vector collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # text-embedding-3-small dimension
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            # Continue anyway - might be connection issue

    def index_text(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Index text into vector database.

        Args:
            doc_id: Unique document identifier
            text: Text content to index
            metadata: Optional metadata dict

        Returns:
            Vector ID
        """
        # Get embedding
        embedding = llm_service.get_embedding(text)

        # Prepare metadata
        payload = {
            "doc_id": doc_id,
            "text": text[:1000],  # Store truncated text in metadata
            **(metadata or {})
        }

        # Create point
        point = PointStruct(
            id=int(hash(doc_id) % (2**63)),  # Convert to int64
            vector=embedding,
            payload=payload
        )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return str(point.id)
        except Exception as e:
            print(f"Error indexing text: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = 8,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar passages.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of result dicts with 'doc_id', 'text', 'score', 'metadata'
        """
        # Get query embedding
        query_embedding = llm_service.get_embedding(query)

        try:
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=None,  # TODO: Implement filter_metadata support
                score_threshold=0.5  # Minimum similarity score
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "doc_id": result.payload.get("doc_id", "unknown"),
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() if k not in ["doc_id", "text"]}
                })

            return formatted_results
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def build_prompt(
        self,
        query: str,
        retrieved_passages: List[Dict[str, Any]],
        template: Optional[str] = None
    ) -> str:
        """
        Build RAG prompt from query and retrieved passages.

        Args:
            query: User query
            retrieved_passages: List of retrieved passage dicts
            template: Optional template name

        Returns:
            Formatted prompt string
        """
        # Build context from retrieved passages
        context_parts = []
        for i, passage in enumerate(retrieved_passages, 1):
            context_parts.append(
                f"[Document {i} - Doc ID: {passage['doc_id']}]\n"
                f"{passage['text']}\n"
                f"(Relevance score: {passage['score']:.2f})\n"
            )

        context = "\n".join(context_parts)

        # Base prompt template
        base_template = """You are VBI Claims Navigator, an expert VA-claims assistant.

Context from client documents:
{context}

User query: {query}

Instructions:
- Use the provided context to answer the query accurately
- Cite specific document IDs when referencing information
- If information is missing, clearly state what is needed
- Never provide legal or medical advice
- Mark any content requiring human review with [HUMAN REVIEW REQUIRED]

Response:"""

        prompt = base_template.format(
            context=context,
            query=query
        )

        # TODO: Add template-specific formatting if template is provided
        if template:
            # Load template from templates/ directory
            pass

        return prompt

    def generate_draft(
        self,
        query: str,
        client_id: int,
        claim_type: str,
        evidence_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Generate a claim draft using RAG.

        Args:
            query: User query/instructions
            client_id: Client ID
            claim_type: Type of claim (e.g., "PTSD")
            evidence_ids: List of document IDs to use as evidence

        Returns:
            Dict with draft_text, evidence_map, confidence, etc.
        """
        # Build search query
        search_query = f"{claim_type} claim {query}"

        # Retrieve relevant passages
        retrieved = self.search(search_query, top_k=8)

        # Filter to only include evidence_ids if provided
        if evidence_ids:
            retrieved = [r for r in retrieved if int(r.get("doc_id", 0)) in evidence_ids]

        # Build prompt
        prompt = self.build_prompt(query, retrieved)

        # Call LLM
        messages = [
            {"role": "system", "content": "You are VBI Claims Navigator. Draft VA claim materials based on provided evidence."},
            {"role": "user", "content": prompt}
        ]

        response = llm_service.call_chat(messages, temperature=0.7)
        draft_text = response["choices"][0]["message"]["content"]

        # Build evidence map
        evidence_map = [
            {
                "doc_id": int(passage.get("doc_id", 0)),
                "excerpt": passage.get("text", "")[:500],
                "supporting_section": passage.get("metadata", {}).get("section", "General"),
                "relevance_score": passage.get("score", 0.0)
            }
            for passage in retrieved[:5]  # Top 5 most relevant
        ]

        # Calculate confidence (simple heuristic - average relevance score)
        confidence = sum(p["score"] for p in retrieved[:5]) / len(retrieved[:5]) if retrieved else 0.5

        return {
            "draft_text": draft_text,
            "evidence_map": evidence_map,
            "human_review_required": True,  # Always require human review
            "confidence": confidence,
            "next_steps": [
                "Review draft for accuracy",
                "Verify all evidence citations",
                "Check for completeness",
                "Obtain accredited agent approval"
            ]
        }


# Global instance
rag_service = RAGService()

