"""
Main FastAPI Application Entrypoint for LegalLens backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.review_router import router as review_router
from app.api.llm_router import router as llm_router
from app.api.graph_router import router as graph_router
from app.api.v1 import api_v1_router, lifespan

app = FastAPI(
    title="LegalLens Knowledge Graph Backend API",
    description=(
        "Backend API for Legal Knowledge Graph Human-in-the-Loop "
        "Review and Local LLM Fallback."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for future React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Step 9 Review router, Step 10 LLM router, Graph router & API v1
app.include_router(review_router)
app.include_router(llm_router)
app.include_router(graph_router)
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "LegalLens API", "step": 10}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
