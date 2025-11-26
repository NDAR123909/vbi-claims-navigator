"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as v1_router
from app.core.config import settings

app = FastAPI(
    title="VBI Claims Navigator API",
    description="VA claims assistant with RAG and document analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v1_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "VBI Claims Navigator API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/.well-known/ai-plugin.json")
async def ai_plugin_manifest():
    """ChatGPT plugin manifest."""
    return {
        "schema_version": "v1",
        "name_for_human": "VBI Claims Navigator",
        "name_for_model": "vbi_claims_navigator",
        "description_for_human": "Expert VA-claims assistant that drafts claim materials, analyzes evidence, and helps navigate the claims process.",
        "description_for_model": "VBI Claims Navigator is an expert VA-claims assistant that drafts claim materials, analyzes evidence for errors/gaps, performs evidence mapping to VASRD and 38 CFR where applicable, searches client records, computes per-client expenses and aggregate business metrics, and surfaces human-review checklists. It never gives legal or medical advice and always marks outputs for human accreditation/review.",
        "auth": {
            "type": "api_key",
            "instructions": "Use the X-API-Key header with your API key."
        },
        "api": {
            "type": "openapi",
            "url": f"{settings.ENVIRONMENT == 'production' and 'https://api.vbi.local' or 'http://localhost:8000'}/openapi.json"
        },
        "contact_email": "support@vbi.local"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

