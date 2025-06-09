from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict

from app.services.llm.client import LLMConfig, LLMProvider


class PDFProcessRequest(BaseModel):
    """Request schema for PDF processing."""

    extract_keys: Optional[List[str]] = Field(
        default=None, description="List of keys to extract from the document"
    )
    custom_prompt: Optional[str] = Field(
        default=None, description="Optional custom prompt for the LLM"
    )


class OCRData(BaseModel):
    """Schema for OCR extracted data."""

    # This is a dynamic model that can have any fields
    # Based on extract_keys or LLM extraction
    model_config = ConfigDict(extra="allow")


class OCRPageResult(BaseModel):
    """Schema for OCR result of a single page."""

    page_number: int = Field(..., description="Page number (1-based)")
    data: OCRData = Field(default_factory=dict, description="Extracted structured data")


class PDFProcessResponse(BaseModel):
    """Response schema for PDF processing."""

    pages: List[OCRPageResult] = Field(
        ..., description="List of OCR results for each page"
    )


class PDFProcessErrorResponse(BaseModel):
    """Error response schema for PDF processing."""

    detail: str = Field(..., description="Error message")


# Schema for LLM configuration validation
class PDFProcessLLMConfig(BaseModel):
    """LLM configuration schema for PDF processing."""

    provider: Optional[str] = Field(
        default=None, description="LLM provider (e.g., 'openai', 'anthropic', 'gemini')"
    )
    model: Optional[str] = Field(default=None, description="LLM model name")
    temperature: Optional[float] = Field(
        default=None, description="Temperature for LLM generation (0.0 to 1.0)"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens for LLM generation"
    )

    def to_llm_config(self) -> LLMConfig:
        """Convert to LLMConfig object."""
        config_data = {}

        if self.provider:
            config_data["provider"] = LLMProvider(self.provider)
        if self.model:
            config_data["model"] = self.model
        if self.temperature is not None:
            config_data["temperature"] = self.temperature
        if self.max_tokens is not None:
            config_data["max_tokens"] = self.max_tokens

        return LLMConfig(**config_data)
