from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import grading

app = FastAPI(
    title="Boundless AI Grading Service",
    description="Advanced AI-powered hackathon submission grading with multi-source evidence analysis, Soroban smart contract verification, and calibrated scoring",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(grading.router)

@app.get("/")
async def root():
    return {
        "message": "Boundless AI Grading Service v2.0 is running",
        "version": "2.0.0",
        "features": [
            "Multi-language repo analysis (Rust, JS/TS, Python, Go)",
            "Soroban smart contract security audit",
            "On-chain Stellar account & contract verification via Soroban RPC",
            "Evidence-based scoring with calibrated rubric",
            "Plagiarism and integrity detection",
            "Batch grading support",
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
