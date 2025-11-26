"""Seed database with sample data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.base import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.claim import Claim, ClaimDocument
from app.services.rag import rag_service
from app.utils.security import encrypt_field
from datetime import date, datetime

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Sample documents text
SAMPLE_DOCS = {
    "dd214": """DEPARTMENT OF DEFENSE
DD FORM 214
CERTIFICATE OF RELEASE OR DISCHARGE FROM ACTIVE DUTY

NAME: John Doe
SSN: 123-45-6789
BRANCH OF SERVICE: US Army
DATE OF ENTRY: 2010-01-15
DATE OF SEPARATION: 2014-03-20
CHARACTER OF SERVICE: Honorable
NATURE OF SEPARATION: Completion of Required Active Service

PRIMARY SPECIALTY: 11B - Infantryman
RANK: E-4 Specialist
TOTAL ACTIVE SERVICE: 4 years, 2 months, 5 days
""",
    "cp_exam": """DEPARTMENT OF VETERANS AFFAIRS
COMPENSATION & PENSION EXAMINATION REPORT

VETERAN: John Doe
DOB: 1985-06-10
EXAM DATE: 2020-05-15
EXAMINER: Dr. Jane Smith, MD

DIAGNOSIS: Post-Traumatic Stress Disorder (PTSD)

HISTORY: Veteran reports experiencing symptoms of PTSD following deployment to Afghanistan in 2012. Symptoms include nightmares, hypervigilance, avoidance of crowds, and difficulty sleeping.

CLINICAL FINDINGS:
- Patient exhibits signs of anxiety and depression
- Reports difficulty maintaining relationships
- Avoids social situations
- Sleep disturbances noted

ASSESSMENT: PTSD, chronic, service-connected
PROGNOSIS: Guarded
""",
    "mri_report": """RADIOLOGY REPORT
MAGNETIC RESONANCE IMAGING (MRI)

PATIENT: John Doe
DOB: 1985-06-10
EXAM DATE: 2020-06-01
REFERRING PHYSICIAN: Dr. Jane Smith

CLINICAL INDICATION: Lower back pain, possible service-related injury

FINDINGS:
- L4-L5 disc herniation noted
- Mild degenerative changes in lumbar spine
- No significant spinal stenosis

IMPRESSION: L4-L5 disc herniation, likely related to service-related activities.

RECOMMENDATIONS: Physical therapy and pain management
""",
    "buddy_letter": """BUDDY STATEMENT
VA FORM 21-4138

STATEMENT IN SUPPORT OF CLAIM

I, Michael Johnson, served with John Doe in Afghanistan from 2012-2013. I witnessed John experiencing significant stress and trauma during our deployment. He was involved in several IED incidents and witnessed combat casualties. After returning home, I noticed significant changes in his behavior including increased anxiety and withdrawal from social activities.

I believe his current PTSD symptoms are directly related to his military service.

Signed: Michael Johnson
Date: 2020-07-10
"""
}


def seed_users():
    """Seed users table."""
    print("Seeding users...")
    
    # Check if users already exist
    if db.query(User).count() > 0:
        print("Users already exist, skipping...")
        return

    users = [
        User(
            email="admin@vbi.local",
            hashed_password="$2b$12$dummy",  # In production, use proper hashing
            full_name="Admin User",
            role=UserRole.ADMIN,
            can_view_phi=True
        ),
        User(
            email="agent@vbi.local",
            hashed_password="$2b$12$dummy",
            full_name="Accredited Agent",
            role=UserRole.ACCREDITED_AGENT,
            can_view_phi=True
        ),
        User(
            email="editor@vbi.local",
            hashed_password="$2b$12$dummy",
            full_name="Editor User",
            role=UserRole.EDITOR,
            can_view_phi=False
        ),
    ]

    for user in users:
        db.add(user)
    db.commit()
    print(f"Created {len(users)} users")


def seed_clients():
    """Seed clients table."""
    print("Seeding clients...")
    
    if db.query(Client).count() > 0:
        print("Clients already exist, skipping...")
        return

    clients = [
        Client(
            first_name_encrypted=encrypt_field("John"),
            last_name_encrypted=encrypt_field("Doe"),
            ssn_encrypted=encrypt_field("123-45-6789"),
            date_of_birth=date(1985, 6, 10),
            client_number="VBI-001",
            branch_of_service="US Army",
            service_start_date=date(2010, 1, 15),
            service_end_date=date(2014, 3, 20),
            meta_data={"service_number": "12345678"}
        ),
        Client(
            first_name_encrypted=encrypt_field("Jane"),
            last_name_encrypted=encrypt_field("Smith"),
            ssn_encrypted=encrypt_field("987-65-4321"),
            date_of_birth=date(1990, 3, 15),
            client_number="VBI-002",
            branch_of_service="US Navy",
            service_start_date=date(2012, 5, 1),
            service_end_date=date(2016, 8, 30),
            meta_data={"service_number": "87654321"}
        ),
    ]

    for client in clients:
        db.add(client)
    db.commit()
    print(f"Created {len(clients)} clients")


def seed_claims():
    """Seed claims and documents."""
    print("Seeding claims and documents...")
    
    if db.query(Claim).count() > 0:
        print("Claims already exist, skipping...")
        return

    # Get first client
    client = db.query(Client).filter(Client.client_number == "VBI-001").first()
    if not client:
        print("Client not found, cannot seed claims")
        return

    # Create claim
    claim = Claim(
        client_id=client.id,
        claim_type="PTSD",
        status="draft",
        human_review_required=True,
        template_used="21-4138_personal_statement"
    )
    db.add(claim)
    db.flush()

    # Create documents
    doc_types = ["dd214", "cp_exam", "mri_report", "buddy_letter"]
    documents = []
    
    for i, doc_type in enumerate(doc_types, 1):
        doc_text = SAMPLE_DOCS[doc_type]
        
        # Index in vector DB
        vector_id = rag_service.index_text(
            doc_id=str(i),
            text=doc_text,
            metadata={"type": doc_type, "client_id": client.id}
        )

        doc = ClaimDocument(
            claim_id=claim.id,
            document_type=doc_type.upper().replace("_", " "),
            file_name=f"{doc_type}.txt",
            ocr_text=doc_text,
            vector_id=vector_id,
            meta_data={"type": doc_type}
        )
        documents.append(doc)
        db.add(doc)

    db.commit()
    print(f"Created 1 claim with {len(documents)} documents")


def main():
    """Main seeding function."""
    print("Starting database seeding...")
    
    try:
        seed_users()
        seed_clients()
        seed_claims()
        print("\nDatabase seeding completed successfully!")
    except Exception as e:
        print(f"\nError seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

