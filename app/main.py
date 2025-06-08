from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from app.schemas.pdf import ErrorResponse, OCRRequest, OCRResponse, OCRResult
from app.services.pdf_service import PDFProcessingError, process_pdf

# Create FastAPI application
app = FastAPI(
    title="Timesheet API",
    description="A minimal FastAPI application with a health check endpoint",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPExceptions to a consistent error response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            message=str(exc.detail),
            detail=None
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions and return a consistent error response."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            message=f"An unexpected error occurred: {str(exc)}",
            detail=None
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify the service is running.
    """
    return HealthResponse(status="ok")


@app.post(
    "/ocr/pdf",
    response_model=OCRResponse,
    responses={
        200: {"model": OCRResponse, "description": "Successfully processed PDF"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        422: {"model": ErrorResponse, "description": "Unprocessable entity"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def process_pdf_file(
    file: UploadFile = File(..., description="PDF file to process"),
    extract_keys: Optional[List[str]] = Form(None, description="List of keys to extract from the document")
) -> OCRResponse:
    """
    Process a PDF file: extract text and structured data using OCR from each page.
    
    - **file**: PDF file to be processed
    - **extract_keys**: Optional list of keys to extract from the document
    
    Returns a list of OCR results with structured data, one for each page in the PDF.
    """
    # Validate file content type
    if not file.content_type or "application/pdf" not in file.content_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File must be a PDF. Received: {file.content_type}",
        )
    
    try:
        # Process the PDF file
        contents = await file.read()
        
        # Process using our service, passing the extract_keys
        results = process_pdf(file.file, extract_keys)
        
        # Create OCR results
        ocr_results = [
            OCRResult(
                page_number=result["page_number"],
                text=result.get("text"),
                confidence=result["confidence"],
                data=result.get("data", {})
            )
            for result in results
        ]
        
        # Return the response
        return OCRResponse(
            status="success",
            message="PDF processed successfully",
            pages_processed=len(ocr_results),
            results=ocr_results
        )
    
    except PDFProcessingError as e:
        # Handle PDF processing errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        # Propagate to the global exception handler
        raise
    finally:
        # Make sure to close the file
        await file.close()


@app.get("/")
async def root():
    """
    Root endpoint redirecting to the health check documentation.
    """
    return {"message": "API is running. See /docs for documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 