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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# PDF processing endpoint
@app.post(
    "/ocr/pdf",
    response_model=PDFProcessResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": PDFProcessErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": PDFProcessErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": PDFProcessErrorResponse},
    },
)
async def process_pdf_route(
    file: UploadFile = File(..., description="PDF file to process"),
    extract_keys: Optional[str] = Form(None, description="Comma-separated list of keys to extract"),
    llm_config_data: Optional[str] = Form(None, description="LLM configuration in JSON format"),
):
    """
    Process a PDF file and extract structured data.
    
    - **file**: PDF file to upload
    - **extract_keys**: Optional comma-separated list of keys to extract from the document
    - **llm_config_data**: Optional LLM configuration in JSON format
    
    Returns a JSON response with OCR results for each page.
    """
    # Validate file content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF",
        )
    
    route_path = "/ocr/pdf"
    
    # Parse extract_keys
    extract_keys_list = None
    if extract_keys:
        extract_keys_list = [k.strip() for k in extract_keys.split(",") if k.strip()]
    
    # Handle LLM config if provided
    if llm_config_data:
        try:
            # Parse the JSON data
            llm_config_dict = json.loads(llm_config_data)
            # Validate with Pydantic model
            llm_config = LLMConfig(**llm_config_dict)
            # Register for the route
            config_manager.register_route_config(route_path, llm_config)
            logger.info(f"Using custom LLM config for request: {llm_config}")
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid LLM configuration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid LLM configuration: {str(e)}",
            )
    
    try:
        # Read file into memory
        file_bytes = await file.read()
        file_obj = io.BytesIO(file_bytes)
        
        # Process the PDF
        results = await process_pdf(
            file=file_obj,
            extract_keys=extract_keys_list,
            route_path=route_path,
        )
        
        # Return results
        return PDFProcessResponse(pages=results)
    
    except PDFProcessingError as e:
        logger.error(f"PDF processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )

@app.get("/")
async def root():
    """
    Root endpoint redirecting to the health check documentation.
    """
    return {"message": "API is running. See /docs for documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 