"""Client service for client lookup and PII access."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.client import Client
from app.models.user import User
from app.utils.security import mask_piis, decrypt_field
from app.utils.audit import log_audit


class ClientService:
    """Service for client operations."""

    @staticmethod
    def get_client(
        db: Session,
        client_id: int,
        user: User,
        reason: str = "Client lookup"
    ) -> Optional[Dict[str, Any]]:
        """
        Get client information with PII handling based on user permissions.

        Args:
            db: Database session
            client_id: Client ID
            user: Current user
            reason: Reason for access (for audit log)

        Returns:
            Client dict with masked/unmasked PII based on permissions
        """
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None

        # Log access
        log_audit(
            db=db,
            user_id=user.id,
            action="view_client",
            resource_type="client",
            resource_id=client_id,
            reason=reason
        )

        # Build response
        client_data = {
            "id": client.id,
            "client_number": client.client_number,
            "branch_of_service": client.branch_of_service,
            "service_start_date": str(client.service_start_date) if client.service_start_date else None,
            "service_end_date": str(client.service_end_date) if client.service_end_date else None,
            "metadata": client.metadata,
            "notes": client.notes,
            "created_at": str(client.created_at),
        }

        # Handle PII based on permissions
        if user.can_view_phi:
            client_data["first_name"] = decrypt_field(client.first_name_encrypted)
            client_data["last_name"] = decrypt_field(client.last_name_encrypted)
            if client.ssn_encrypted:
                client_data["ssn"] = decrypt_field(client.ssn_encrypted)
            client_data["date_of_birth"] = str(client.date_of_birth) if client.date_of_birth else None
        else:
            # Mask PII
            if client.first_name_encrypted:
                client_data["first_name"] = mask_piis(decrypt_field(client.first_name_encrypted))
            if client.last_name_encrypted:
                client_data["last_name"] = mask_piis(decrypt_field(client.last_name_encrypted))
            if client.ssn_encrypted:
                client_data["ssn"] = mask_piis(decrypt_field(client.ssn_encrypted))
            client_data["date_of_birth"] = "****-**-**" if client.date_of_birth else None

        return client_data

    @staticmethod
    def search_clients(
        db: Session,
        query: str,
        user: User,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Search clients by client number or other metadata.

        Args:
            db: Database session
            query: Search query
            user: Current user
            limit: Maximum results

        Returns:
            List of client dicts (with masked PII if user lacks permission)
        """
        # Simple search by client number
        clients = db.query(Client).filter(
            Client.client_number.ilike(f"%{query}%")
        ).limit(limit).all()

        results = []
        for client in clients:
            client_data = ClientService.get_client(db, client.id, user, reason="Client search")
            if client_data:
                results.append(client_data)

        return results

