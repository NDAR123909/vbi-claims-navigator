"""Background worker tasks using RQ."""
from rq import Queue
from redis import Redis
from app.core.config import settings
from app.services.ocr import ocr_service
from app.services.rag import rag_service
from app.services.llm import llm_service

redis_conn = Redis.from_url(settings.REDIS_URL)
task_queue = Queue('default', connection=redis_conn)


def process_ocr_task(file_path: str, doc_id: str) -> dict:
    """
    Background task for OCR processing.

    Args:
        file_path: Path to file
        doc_id: Document ID

    Returns:
        OCR result dict
    """
    result = ocr_service.extract_text(file_path)
    
    # Index extracted text in vector DB
    if result["text"]:
        vector_id = rag_service.index_text(
            doc_id=doc_id,
            text=result["text"],
            metadata={"source": file_path, "method": result["method"]}
        )
        result["vector_id"] = vector_id

    return result


def batch_embed_documents(documents: list[dict]) -> list[dict]:
    """
    Background task for batch embedding.

    Args:
        documents: List of {doc_id, text} dicts

    Returns:
        List of {doc_id, vector_id} dicts
    """
    results = []
    for doc in documents:
        vector_id = rag_service.index_text(
            doc_id=doc["doc_id"],
            text=doc["text"],
            metadata=doc.get("metadata", {})
        )
        results.append({
            "doc_id": doc["doc_id"],
            "vector_id": vector_id
        })
    return results


def generate_long_draft(request_data: dict) -> dict:
    """
    Background task for generating long drafts (async).

    Args:
        request_data: Draft request data

    Returns:
        Draft result dict
    """
    from app.services.rag import rag_service
    
    return rag_service.generate_draft(
        query=request_data.get("query", ""),
        client_id=request_data["client_id"],
        claim_type=request_data["claim_type"],
        evidence_ids=request_data.get("evidence_ids", [])
    )

