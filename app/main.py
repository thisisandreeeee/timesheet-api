import io
import json
import logging
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.schemas.pdf import (
    PDFProcessErrorResponse,
    PDFProcessLLMConfig,
    PDFProcessResponse,
)
from app.services.pdf_service import PDFProcessingError, process_pdf
from app.services.llm.config import config_manager
from app.services.llm.client import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Timesheet API",
    description="API for processing timesheet data",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ocr_routes.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    Root endpoint redirecting to the health check documentation.
    """
    return {"message": "API is running. See /docs for documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
