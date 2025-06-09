from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class EmployeeBase(BaseModel):
    """Base schema for employee data."""

    staff_code: str = Field(..., description="Unique staff code")
    name: str = Field(..., description="Employee name")

    @field_validator("staff_code")
    @classmethod
    def validate_staff_code(cls, v: str) -> str:
        """Validate that staff code is not empty."""
        if not v.strip():
            raise ValueError("Staff code cannot be empty")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""

    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""

    staff_code: str | None = Field(None, description="Unique staff code")
    name: str | None = Field(None, description="Employee name")

    @field_validator("staff_code")
    @classmethod
    def validate_staff_code(cls, v: str | None) -> str | None:
        """Validate that staff code is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Staff code cannot be empty")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate that name is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty")
        return v


class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""

    uuid: UUID = Field(..., description="Employee UUID")

    class Config:
        from_attributes = True
