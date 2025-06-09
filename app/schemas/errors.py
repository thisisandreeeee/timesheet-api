from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Base error response schema."""
    detail: str = Field(..., description="Error detail message")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response schema."""
    pass


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response schema."""
    pass


class ConflictErrorResponse(ErrorResponse):
    """Conflict error response schema."""
    pass 