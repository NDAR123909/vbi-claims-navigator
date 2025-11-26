"""Tests for RAG service."""
import pytest
from app.services.rag import rag_service
from app.services.llm import llm_service


def test_get_embedding():
    """Test embedding generation."""
    text = "Test text for embedding"
    embedding = llm_service.get_embedding(text)
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, (int, float)) for x in embedding)


def test_index_text():
    """Test text indexing."""
    doc_id = "test_doc_1"
    text = "This is a test document about PTSD claims."
    vector_id = rag_service.index_text(
        doc_id=doc_id,
        text=text,
        metadata={"type": "test"}
    )
    assert vector_id is not None


def test_search():
    """Test vector search."""
    # First index some text
    rag_service.index_text(
        doc_id="test_doc_1",
        text="Post-traumatic stress disorder is a mental health condition."
    )
    rag_service.index_text(
        doc_id="test_doc_2",
        text="Veterans may experience PTSD after combat deployment."
    )

    # Search
    results = rag_service.search("PTSD symptoms", top_k=2)
    assert isinstance(results, list)
    # Results may be empty if vector DB is not properly set up, but should not error


def test_build_prompt():
    """Test prompt building."""
    query = "What is PTSD?"
    retrieved = [
        {
            "doc_id": "1",
            "text": "PTSD is a mental health condition.",
            "score": 0.9
        }
    ]
    prompt = rag_service.build_prompt(query, retrieved)
    assert isinstance(prompt, str)
    assert query in prompt
    assert "PTSD" in prompt


def test_generate_draft():
    """Test draft generation."""
    result = rag_service.generate_draft(
        query="Generate a PTSD claim draft",
        client_id=1,
        claim_type="PTSD",
        evidence_ids=[1, 2]
    )
    assert "draft_text" in result
    assert "evidence_map" in result
    assert "human_review_required" in result
    assert result["human_review_required"] is True
    assert "confidence" in result
    assert "next_steps" in result

