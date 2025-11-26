"""Finance service for expense and metrics computation."""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.client import Client
from app.models.claim import Claim
from datetime import datetime, timedelta


class FinanceService:
    """Service for financial computations."""

    @staticmethod
    def compute_client_expenses(
        db: Session,
        client_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Compute expenses for a specific client.

        Args:
            db: Database session
            client_id: Client ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with expense breakdown
        """
        # TODO: Implement actual expense calculation logic
        # This would query expense records, calculate totals by category, etc.

        # Placeholder implementation
        return {
            "client_id": client_id,
            "period": {
                "start": str(start_date) if start_date else None,
                "end": str(end_date) if end_date else None
            },
            "total_expenses": 0.0,
            "by_category": {},
            "by_month": {},
            "currency": "USD"
        }

    @staticmethod
    def compute_business_metrics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Compute aggregate business KPIs.

        Args:
            db: Database session
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dict with business metrics
        """
        # Build query filters
        query = db.query(Claim)
        if start_date:
            query = query.filter(Claim.created_at >= start_date)
        if end_date:
            query = query.filter(Claim.created_at <= end_date)

        # Count claims by status
        claims = query.all()
        status_counts = {}
        for claim in claims:
            status_counts[claim.status] = status_counts.get(claim.status, 0) + 1

        # Count total clients
        total_clients = db.query(func.count(Client.id)).scalar()

        # Average confidence score
        avg_confidence = db.query(func.avg(Claim.confidence_score)).filter(
            Claim.confidence_score.isnot(None)
        ).scalar() or 0.0

        # Claims requiring review
        claims_needing_review = db.query(func.count(Claim.id)).filter(
            Claim.human_review_required == True
        ).scalar()

        return {
            "period": {
                "start": str(start_date) if start_date else None,
                "end": str(end_date) if end_date else None
            },
            "total_clients": total_clients,
            "total_claims": len(claims),
            "claims_by_status": status_counts,
            "average_confidence_score": float(avg_confidence),
            "claims_requiring_review": claims_needing_review,
            "claims_finalized": db.query(func.count(Claim.id)).filter(
                Claim.finalized_at.isnot(None)
            ).scalar()
        }

