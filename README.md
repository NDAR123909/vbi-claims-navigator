# VBI Claims Navigator

Expert VA-claims assistant that drafts claim materials, analyzes evidence for errors/gaps, performs evidence mapping to VASRD and 38 CFR where applicable, searches client records, computes per-client expenses and aggregate business metrics, and surfaces human-review checklists.

## Features

- **RAG-Powered Draft Generation**: Generate claim drafts using retrieval-augmented generation
- **Document Analysis**: OCR and error detection for claim documents
- **Evidence Mapping**: Map evidence to VASRD and 38 CFR
- **Client Management**: Secure client lookup with PII/PHI encryption
- **Expense Tracking**: Compute per-client expenses and business metrics
- **Audit Logging**: Comprehensive audit trail for all PHI access
- **RBAC**: Role-based access control (reader, editor, accredited_agent, admin)
- **ChatGPT Integration**: OpenAPI plugin manifest for ChatGPT integration

## Architecture

```
ChatGPT Custom GPT/Plugin
    ↓
Public API Gateway (FastAPI)
    ↓
FastAPI Backend
    ├─ /api/v1/query - Main conversational endpoint
    ├─ /api/v1/draft - Claim draft generator
    ├─ /api/v1/embeddings - Vector embeddings
    ├─ /api/v1/retrieve - Vector search
    ├─ /api/v1/ocr - Document OCR
    ├─ /api/v1/client/{id} - Client lookup
    ├─ /api/v1/compute/expenses - Expense computation
    ├─ /api/v1/compute/metrics - Business KPIs
    └─ /api/v1/audit/logs - Audit logs
    ↓
Postgres (Primary DB) + Qdrant (Vector DB) + Redis (Queue)
```

## Tech Stack

- **Python 3.11+**
- **FastAPI** - API framework
- **Postgres** - Primary database
- **Qdrant** - Vector database for RAG
- **Redis + RQ** - Background job queue
- **OpenAI API** - LLM and embeddings
- **Tesseract** - OCR (with optional AWS Textract)
- **SQLAlchemy + Alembic** - ORM and migrations
- **Docker + docker-compose** - Containerization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (optional - uses mock LLM if not provided)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd vbi-claims-navigator
# Copy environment file (Windows: copy env.example .env | Linux/Mac: cp env.example .env)
copy env.example .env
# Edit .env with your configuration
```

### 2. Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- Postgres (port 5432)
- Redis (port 6379)
- Qdrant (ports 6333, 6334)
- FastAPI app (port 8000)
- Worker (background tasks)

### 3. Run Database Migrations

```bash
docker-compose exec app alembic upgrade head
```

### 4. Seed Sample Data

```bash
docker-compose exec app python seed_db.py
```

This creates:
- 3 sample users (admin, agent, editor)
- 2 sample clients
- 1 sample claim with 4 documents
- Indexes documents in vector DB

### 5. Access the API

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Plugin Manifest: http://localhost:8000/.well-known/ai-plugin.json

## Local Development (Without Docker)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Services

You'll need to run Postgres, Redis, and Qdrant separately:

```bash
# Postgres (if installed locally)
pg_ctl start

# Redis (if installed locally)
redis-server

# Qdrant (using Docker)
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Set Environment Variables

```bash
export DATABASE_URL="postgresql://vbi_user:vbi_pass@localhost:5432/vbi_claims"
export REDIS_URL="redis://localhost:6379/0"
export QDRANT_URL="http://localhost:6333"
export OPENAI_API_KEY="your-key-here"  # Optional
export API_KEY="test-api-key"
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Seed Database

```bash
python seed_db.py
```

### 6. Start Application

```bash
uvicorn app.main:app --reload
```

### 7. Start Worker (Separate Terminal)

```bash
python -m app.workers.runner
```

## API Usage Examples

### Query Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "What evidence is needed for a PTSD claim?",
    "client_id": 1
  }'
```

### Draft Generation

```bash
curl -X POST http://localhost:8000/api/v1/draft \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "client_id": 1,
    "claim_type": "PTSD",
    "evidence_ids": [1, 2, 3],
    "template": "21-4138_personal_statement"
  }'
```

### Get Client

```bash
curl -X GET http://localhost:8000/api/v1/client/1 \
  -H "X-API-Key: test-api-key"
```

### Compute Metrics

```bash
curl -X POST http://localhost:8000/api/v1/compute/metrics \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{}'
```

### OCR Document

```bash
curl -X POST http://localhost:8000/api/v1/ocr \
  -H "X-API-Key: test-api-key" \
  -F "file=@document.pdf"
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest app/tests/test_api.py
```

### Integration Test Example

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run tests
pytest app/tests/test_api.py::test_draft_endpoint -v
```

## ChatGPT Integration

### Option A: Custom GPT (Simple)

1. Deploy your backend to a public URL (e.g., https://api.vbi.local)
2. In ChatGPT Custom GPT builder:
   - Add system prompt (see `docs/system_prompt.txt`)
   - Add action/tool that calls your `/api/v1/query` endpoint
   - Configure authentication (API key)

### Option B: ChatGPT Plugin (Production)

1. Ensure your backend is publicly accessible
2. The plugin manifest is available at `/.well-known/ai-plugin.json`
3. Register the plugin in ChatGPT:
   - Go to ChatGPT → Settings → Beta features → Plugins
   - Add your plugin URL
   - ChatGPT will use the OpenAPI spec at `/openapi.json`

### System Prompt for Custom GPT

```
You are VBI Claims Navigator — an assistant for the VBI team. Your goals: help staff draft high-quality veteran claims, detect document errors and evidence gaps, search client files from company databases, compute per-client expenses and business metrics, and provide clear human-review checklists for every draft. 

Hard rules: never provide legal advice, never provide medical diagnoses, always mark any text that must be reviewed by an accredited agent with [HUMAN REVIEW REQUIRED]. Use company knowledge files (provided) before making external assumptions. If a user requests client data, require user confirmation of client ID and check RBAC before returning PHI. 

Always produce: (1) summary, (2) evidence map (doc ids + excerpts), (3) draft text, (4) clear list of next steps for human reviewer.
```

## Security & HIPAA Compliance

### Encryption

- **TLS**: All transport encrypted (use HTTPS in production)
- **At Rest**: PII/PHI fields encrypted using Fernet (AES-256)
- **Secrets**: Store API keys in environment variables or secrets manager

### Access Control

- **RBAC**: Role-based access (reader, editor, accredited_agent, admin)
- **PHI Access**: Only users with `can_view_phi=True` can view unencrypted PII
- **API Keys**: Required for all endpoints

### Audit Logging

- All PHI access logged with user, timestamp, IP, reason
- Immutable audit trail in `audit_logs` table
- Access via `/api/v1/audit/logs` (admin only)

### Data Minimization

- PII masked in logs using `mask_piis()` utility
- Only decrypt PHI in memory when necessary
- No PHI in error messages or logs

### Business Associate Agreements (BAA)

⚠️ **Important**: Before sending PHI to third-party services (OpenAI, Pinecone, etc.), ensure:
1. BAA is signed, OR
2. Use self-hosted alternatives (on-prem LLM/embeddings)

If BAA is not available, do NOT send PHI to those services.

## Project Structure

```
vbi-claims-navigator/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── routes.py    # API endpoints
│   │       ├── schemas.py   # Pydantic schemas
│   │       └── deps.py      # Dependencies (auth, rate limiting)
│   ├── services/
│   │   ├── llm.py           # LLM wrapper (OpenAI)
│   │   ├── rag.py           # RAG service
│   │   ├── ocr.py           # OCR service
│   │   ├── client.py        # Client service
│   │   └── finance.py       # Finance service
│   ├── models/
│   │   ├── user.py          # User model
│   │   ├── client.py        # Client model
│   │   └── claim.py         # Claim models
│   ├── db/
│   │   ├── base.py          # DB base
│   │   └── session.py       # Session management
│   ├── workers/
│   │   ├── tasks.py         # Background tasks
│   │   └── runner.py        # Worker runner
│   ├── utils/
│   │   ├── security.py      # Encryption, PII masking
│   │   └── audit.py         # Audit logging
│   └── tests/
│       ├── test_api.py      # API tests
│       ├── test_rag.py      # RAG tests
│       └── test_llm.py      # LLM tests
├── alembic/                 # Database migrations
├── docker-compose.yml       # Docker services
├── Dockerfile              # App container
├── seed_db.py              # Database seeding
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Environment Variables

See `env.example` for all configuration options. Key variables:

- `DATABASE_URL` - Postgres connection string
- `REDIS_URL` - Redis connection string
- `QDRANT_URL` - Qdrant vector DB URL
- `OPENAI_API_KEY` - OpenAI API key (optional - uses mock if not set)
- `API_KEY` - API key for authentication
- `SECRET_KEY` - Secret key for encryption
- `ENCRYPTION_KEY` - Key for PII/PHI encryption

## Deployment Checklist

- [ ] Set up production database (managed Postgres)
- [ ] Configure secrets manager (Vault/AWS Secrets Manager)
- [ ] Enable HTTPS (load balancer/Cloudflare)
- [ ] Set up monitoring (Sentry, Prometheus, Grafana)
- [ ] Configure backups (Postgres + vector DB)
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Verify BAA for third-party services
- [ ] Run security audit and penetration testing
- [ ] Configure rate limiting (Redis-based)
- [ ] Set up log aggregation (ELK/CloudWatch)
- [ ] Test disaster recovery procedures

## Development Roadmap

- [ ] Implement document error detection (date/name mismatches)
- [ ] Add VASRD/38 CFR mapping logic
- [ ] Implement expense tracking (full logic)
- [ ] Add template system for claim forms
- [ ] Implement JWT authentication
- [ ] Add streaming responses for long drafts
- [ ] Implement Redis-based rate limiting
- [ ] Add comprehensive error handling
- [ ] Implement document comparison utilities
- [ ] Add historical analytics dashboard

## License

Proprietary - VBI Internal Use Only

## Support

For issues or questions, contact: support@vbi.local

