"""
Main FastAPI Application Entrypoint for LegalLens backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.review_router import router as review_router

app = FastAPI(
    title="LegalLens Knowledge Graph Backend API",
    description="Backend API for Legal Knowledge Graph Human-in-the-Loop Review and Correction.",
    version="1.0.0",
)

# Configure CORS for future React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Step 9 Review router
app.include_router(review_router)


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "LegalLens API", "step": 9}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
