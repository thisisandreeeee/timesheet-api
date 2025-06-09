import io
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.schemas.pdf import (
    PDFProcessErrorResponse,
    PDFProcessResponse,
)
from app.services.pdf_service import PDFProcessingError, process_pdf
from app.services.llm.config import config_manager
from app.services.llm.client import LLMConfig

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post(
    "/pdf",
    response_model=PDFProcessResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": PDFProcessErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": PDFProcessErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": PDFProcessErrorResponse},
    },
    summary="Process PDF with OCR",
    description="Extract structured data from PDF files using OCR and LLM processing.",
)
async def process_pdf_route(
    file: UploadFile = File(..., description="PDF file to process"),
    llm_config_data: Optional[str] = Form(
        None, description="LLM configuration in JSON format"
    ),
):
    """
    Process a PDF file and extract structured data.

    - **file**: PDF file to upload
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
