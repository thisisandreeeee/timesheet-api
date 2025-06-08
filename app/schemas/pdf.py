from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """Schema for OCR result of a single page."""
    page_number: int = Field(..., description="Page number in the original PDF")
    text: Optional[str] = Field(None, description="Extracted text from OCR")
    confidence: str = Field(..., description="Confidence level of the OCR result")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dictionary containing extracted data")


class OCRResponse(BaseModel):
    """Schema for OCR processing response."""
    status: str = Field("success", description="Processing status")
    message: Optional[str] = Field(None, description="Additional information")
    pages_processed: int = Field(..., description="Number of pages processed")
    results: List[OCRResult] = Field(..., description="List of OCR results per page")


class OCRRequest(BaseModel):
    """Schema for OCR processing request parameters."""
    extract_keys: Optional[List[str]] = Field(
        None, 
        description="List of keys to extract from the document. If not provided, all possible keys will be extracted."
    )


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    status: str = Field("error", description="Error status")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information") 