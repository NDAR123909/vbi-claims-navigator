"""API v1 routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.api.v1.deps import get_api_key, rate_limit, get_current_user
from app.api.v1.schemas import (
    QueryRequest, QueryResponse,
    EmbeddingRequest, EmbeddingResponse,
    RetrieveRequest, RetrieveResponse,
    DraftRequest, DraftResponse,
    OCRRequest, OCRResponse,
    ClientResponse,
    ExpenseRequest, ExpenseResponse,
    MetricsRequest, MetricsResponse
)
from app.services.llm import llm_service
from app.services.rag import rag_service
from app.services.ocr import ocr_service
from app.services.client import ClientService
from app.services.finance import FinanceService
from app.models.user import User
from app.models.claim import AuditLog
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Main conversational query endpoint.
    """
    # Log access
    log_audit(
        db=db,
        user_id=user.id,
        action="query",
        resource_type="query",
        reason=f"Query: {request.query[:100]}"
    )

    # Use RAG to get answer
    retrieved = rag_service.search(request.query, top_k=5)
    prompt = rag_service.build_prompt(request.query, retrieved)

    messages = [
        {"role": "system", "content": "You are VBI Claims Navigator. Answer questions based on provided context."},
        {"role": "user", "content": prompt}
    ]

    response = llm_service.call_chat(messages)
    answer = response["choices"][0]["message"]["content"]

    # Calculate confidence from retrieved passages
    confidence = sum(r["score"] for r in retrieved) / len(retrieved) if retrieved else 0.5

    return QueryResponse(
        answer=answer,
        sources=[{"doc_id": r["doc_id"], "score": r["score"]} for r in retrieved],
        confidence=min(confidence, 1.0)
    )


@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Create and store embedding.
    """
    embedding = llm_service.get_embedding(request.text)
    vector_id = None

    if request.doc_id:
        # Index in vector DB
        vector_id = rag_service.index_text(
            doc_id=request.doc_id,
            text=request.text
        )

    return EmbeddingResponse(
        embedding=embedding,
        doc_id=request.doc_id,
        vector_id=vector_id
    )


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(
    request: RetrieveRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Retrieve candidate passages from vector DB.
    """
    results = rag_service.search(request.query, top_k=request.top_k)

    return RetrieveResponse(results=results)


@router.post("/draft", response_model=DraftResponse)
async def draft_claim(
    request: DraftRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Generate claim draft using RAG.
    """
    # Log access
    log_audit(
        db=db,
        user_id=user.id,
        action="create_draft",
        resource_type="claim",
        resource_id=None,
        reason=f"Draft for client {request.client_id}, claim type: {request.claim_type}"
    )

    # Generate draft
    draft_result = rag_service.generate_draft(
        query=f"Generate a {request.claim_type} claim draft",
        client_id=request.client_id,
        claim_type=request.claim_type,
        evidence_ids=request.evidence_ids
    )

    return DraftResponse(**draft_result)


@router.post("/ocr", response_model=OCRResponse)
async def ocr_document(
    file: UploadFile = File(...),
    use_textract: bool = False,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Perform OCR on uploaded document.
    """
    # Save uploaded file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        result = ocr_service.extract_text(tmp_path, use_textract=use_textract)
        return OCRResponse(**result)
    finally:
        # Clean up
        os.unlink(tmp_path)


@router.get("/client/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Get client information.
    """
    client_data = ClientService.get_client(db, client_id, user, reason="API client lookup")
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse(**client_data)


@router.post("/compute/expenses", response_model=ExpenseResponse)
async def compute_expenses(
    request: ExpenseRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Compute client expenses.
    """
    expenses = FinanceService.compute_client_expenses(
        db=db,
        client_id=request.client_id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return ExpenseResponse(**expenses)


@router.post("/compute/metrics", response_model=MetricsResponse)
async def compute_metrics(
    request: MetricsRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Compute business KPIs.
    """
    metrics = FinanceService.compute_business_metrics(
        db=db,
        start_date=request.start_date,
        end_date=request.end_date
    )
    return MetricsResponse(**metrics)


@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(rate_limit),
    user: User = Depends(get_current_user)
):
    """
    Get audit logs (admin only).
    """
    # Check if user is admin
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "timestamp": str(log.timestamp),
            "reason": log.reason
        }
        for log in logs
    ]

