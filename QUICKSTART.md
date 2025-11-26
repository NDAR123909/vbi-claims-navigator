# Quick Start Guide

## 1. Initial Setup (5 minutes)

```bash
# Copy environment file (Windows: copy env.example .env | Linux/Mac: cp env.example .env)
copy env.example .env

# Edit .env and add your OpenAI API key (optional - uses mock if not set)
# At minimum, change API_KEY and ENCRYPTION_KEY for security
```

## 2. Start Everything with Docker (2 minutes)

```bash
docker-compose up -d
```

Wait ~30 seconds for services to start, then:

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Seed sample data
docker-compose exec app python seed_db.py
```

## 3. Test the API (1 minute)

```bash
# Health check
curl http://localhost:8000/health

# Test query (uses mock LLM if no OpenAI key)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{"query": "What is PTSD?"}'
```

## 4. View API Documentation

Open in browser: http://localhost:8000/docs

## 5. Test Draft Generation

```bash
curl -X POST http://localhost:8000/api/v1/draft \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "client_id": 1,
    "claim_type": "PTSD",
    "evidence_ids": [1, 2],
    "template": "21-4138_personal_statement"
  }'
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [docs/system_prompt.txt](docs/system_prompt.txt) for ChatGPT integration
- Run tests: `pytest`
- Check logs: `docker-compose logs -f app`

## Troubleshooting

**Services won't start?**
```bash
docker-compose down
docker-compose up -d
docker-compose logs
```

**Database connection errors?**
- Wait a bit longer for Postgres to initialize
- Check `docker-compose ps` to see if all services are running

**Vector DB errors?**
- Qdrant may take a moment to initialize
- Check `docker-compose logs qdrant`

