"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Query schemas
class QueryRequest(BaseModel):
    """Query request schema."""
    query: str = Field(..., description="User query")
    client_id: Optional[int] = Field(None, description="Optional client ID for context")


class QueryResponse(BaseModel):
    """Query response schema."""
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


# Embedding schemas
class EmbeddingRequest(BaseModel):
    """Embedding request schema."""
    text: str = Field(..., description="Text to embed")
    doc_id: Optional[str] = Field(None, description="Optional document ID")


class EmbeddingResponse(BaseModel):
    """Embedding response schema."""
    embedding: List[float]
    doc_id: Optional[str] = None
    vector_id: Optional[str] = None


# Retrieve schemas
class RetrieveRequest(BaseModel):
    """Retrieve request schema."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(8, ge=1, le=50, description="Number of results")


class RetrieveResponse(BaseModel):
    """Retrieve response schema."""
    results: List[Dict[str, Any]]


# Draft schemas
class DraftRequest(BaseModel):
    """Draft request schema."""
    client_id: int = Field(..., description="Client ID")
    claim_type: str = Field(..., description="Type of claim (e.g., PTSD, Tinnitus)")
    evidence_ids: List[int] = Field(default_factory=list, description="List of document IDs")
    template: Optional[str] = Field(None, description="Template name (e.g., 21-4138_personal_statement)")


class EvidenceMapItem(BaseModel):
    """Evidence map item schema."""
    doc_id: int
    excerpt: str
    supporting_section: str
    relevance_score: Optional[float] = None


class DraftResponse(BaseModel):
    """Draft response schema."""
    draft_text: str
    evidence_map: List[EvidenceMapItem]
    human_review_required: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    next_steps: List[str] = Field(default_factory=list)


# OCR schemas
class OCRRequest(BaseModel):
    """OCR request schema."""
    file_path: str = Field(..., description="Path to file")
    use_textract: Optional[bool] = Field(None, description="Force use of Textract")


class OCRResponse(BaseModel):
    """OCR response schema."""
    text: str
    method: str
    confidence: Optional[float] = None


# Client schemas
class ClientResponse(BaseModel):
    """Client response schema."""
    id: int
    client_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ssn: Optional[str] = None
    date_of_birth: Optional[str] = None
    branch_of_service: Optional[str] = None
    service_start_date: Optional[str] = None
    service_end_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: str


# Expense schemas
class ExpenseRequest(BaseModel):
    """Expense request schema."""
    client_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExpenseResponse(BaseModel):
    """Expense response schema."""
    client_id: int
    period: Dict[str, Optional[str]]
    total_expenses: float
    by_category: Dict[str, float]
    by_month: Dict[str, float]
    currency: str = "USD"


# Metrics schemas
class MetricsRequest(BaseModel):
    """Metrics request schema."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class MetricsResponse(BaseModel):
    """Metrics response schema."""
    period: Dict[str, Optional[str]]
    total_clients: int
    total_claims: int
    claims_by_status: Dict[str, int]
    average_confidence_score: float
    claims_requiring_review: int
    claims_finalized: int

