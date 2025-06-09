from typing import List
from uuid import UUID

import aiosqlite
from fastapi import APIRouter, Depends, Path, status

from app.database import get_db
from app.schemas.errors import ConflictErrorResponse, NotFoundErrorResponse
from app.schemas.timesheet import TimesheetCreate, TimesheetResponse, TimesheetUpdate
from app.services import timesheet_service

router = APIRouter(tags=["timesheets"])


@router.get(
    "/employees/{uuid}/timesheets",
    response_model=List[TimesheetResponse],
    summary="List all timesheets for an employee",
    description="Retrieve a list of all timesheets for a specific employee.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def get_employee_timesheets(
    uuid: UUID, conn: aiosqlite.Connection = Depends(get_db)
):
    """Get all timesheets for an employee."""
    timesheets = await timesheet_service.get_employee_timesheets(conn, uuid)
    return timesheets


@router.get(
    "/employees/{uuid}/timesheets/{year}/{month}",
    response_model=TimesheetResponse,
    summary="Get specific timesheet",
    description="Retrieve a specific timesheet for an employee by year and month.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def get_employee_timesheet(
    uuid: UUID,
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Get a specific timesheet for an employee."""
    return await timesheet_service.get_employee_timesheet(conn, uuid, year, month)


@router.post(
    "/employees/{uuid}/timesheets",
    response_model=TimesheetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new timesheet",
    description="Create a new timesheet for a specific employee.",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ConflictErrorResponse},
    },
)
async def create_employee_timesheet(
    uuid: UUID, timesheet: TimesheetCreate, conn: aiosqlite.Connection = Depends(get_db)
):
    """Create a new timesheet for an employee."""
    return await timesheet_service.create_employee_timesheet(conn, uuid, timesheet)


@router.put(
    "/employees/{uuid}/timesheets/{year}/{month}",
    response_model=TimesheetResponse,
    summary="Update timesheet",
    description="Update a specific timesheet for an employee.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def update_employee_timesheet(
    uuid: UUID,
    timesheet: TimesheetUpdate,
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Update a specific timesheet for an employee."""
    return await timesheet_service.update_employee_timesheet(
        conn, uuid, year, month, timesheet
    )


@router.delete(
    "/employees/{uuid}/timesheets/{year}/{month}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete timesheet",
    description="Delete a specific timesheet for an employee.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def delete_employee_timesheet(
    uuid: UUID,
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Delete a specific timesheet for an employee."""
    await timesheet_service.delete_employee_timesheet(conn, uuid, year, month)
    return None
