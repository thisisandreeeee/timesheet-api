from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator


class TimesheetBase(BaseModel):
    """Base schema for timesheet data."""

    year: int = Field(..., description="Year of the timesheet", ge=2000, le=2100)
    month: int = Field(..., description="Month of the timesheet", ge=1, le=12)
    total_working_days: int = Field(..., description="Total working days", ge=0)
    total_ot_hours: float = Field(..., description="Total overtime hours", ge=0)
    total_sundays_worked: int = Field(..., description="Total Sundays worked", ge=0)
    total_ot_hours_on_sundays: float = Field(
        ..., description="Total overtime hours on Sundays", ge=0
    )

    @model_validator(mode="after")
    def validate_sundays_vs_working_days(self) -> "TimesheetBase":
        """Validate that total Sundays worked is not more than total working days."""
        if self.total_sundays_worked > self.total_working_days:
            raise ValueError("Total Sundays worked cannot exceed total working days")
        return self


class TimesheetCreate(TimesheetBase):
    """Schema for creating a timesheet."""

    pass


class TimesheetUpdate(BaseModel):
    """Schema for updating a timesheet."""

    total_working_days: int | None = Field(None, description="Total working days", ge=0)
    total_ot_hours: float | None = Field(None, description="Total overtime hours", ge=0)
    total_sundays_worked: int | None = Field(
        None, description="Total Sundays worked", ge=0
    )
    total_ot_hours_on_sundays: float | None = Field(
        None, description="Total overtime hours on Sundays", ge=0
    )

    @model_validator(mode="after")
    def validate_sundays_vs_working_days(self) -> "TimesheetUpdate":
        """Validate that total Sundays worked is not more than total working days."""
        if (
            self.total_sundays_worked is not None
            and self.total_working_days is not None
            and self.total_sundays_worked > self.total_working_days
        ):
            raise ValueError("Total Sundays worked cannot exceed total working days")
        return self


class TimesheetResponse(TimesheetBase):
    """Schema for timesheet response."""

    id: int = Field(..., description="Timesheet ID")
    employee_uuid: UUID = Field(..., description="Employee UUID")

    class Config:
        from_attributes = True
