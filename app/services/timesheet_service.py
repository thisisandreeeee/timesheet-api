from typing import Dict, List
from uuid import UUID

import aiosqlite
from fastapi import HTTPException, status

from app.repositories import timesheet_repository
from app.schemas.timesheet import TimesheetCreate, TimesheetUpdate
from app.services.employee_service import get_employee


async def get_employee_timesheets(conn: aiosqlite.Connection, employee_uuid: UUID) -> List[Dict]:
    """
    Get all timesheets for an employee.
    
    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        
    Returns:
        List of timesheet records
        
    Raises:
        HTTPException: If employee not found
    """
    # Verify employee exists
    await get_employee(conn, employee_uuid)
    
    return await timesheet_repository.get_timesheets_by_employee(conn, employee_uuid)


async def get_employee_timesheet(
    conn: aiosqlite.Connection, employee_uuid: UUID, year: int, month: int
) -> Dict:
    """
    Get a specific timesheet.
    
    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet
        
    Returns:
        Timesheet record
        
    Raises:
        HTTPException: If employee or timesheet not found
    """
    # Verify employee exists
    await get_employee(conn, employee_uuid)
    
    timesheet = await timesheet_repository.get_timesheet(conn, employee_uuid, year, month)
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timesheet for employee {employee_uuid}, year {year}, month {month} not found"
        )
    
    return timesheet


async def create_employee_timesheet(
    conn: aiosqlite.Connection, employee_uuid: UUID, timesheet: TimesheetCreate
) -> Dict:
    """
    Create a new timesheet.
    
    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        timesheet: Timesheet data
        
    Returns:
        Created timesheet record
        
    Raises:
        HTTPException: If employee not found or timesheet already exists
    """
    # Verify employee exists
    await get_employee(conn, employee_uuid)
    
    # Check if timesheet already exists
    existing_timesheet = await timesheet_repository.get_timesheet(
        conn, employee_uuid, timesheet.year, timesheet.month
    )
    if existing_timesheet:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Timesheet for employee {employee_uuid}, year {timesheet.year}, month {timesheet.month} already exists"
        )
    
    return await timesheet_repository.create_timesheet(conn, employee_uuid, timesheet)


async def update_employee_timesheet(
    conn: aiosqlite.Connection,
    employee_uuid: UUID,
    year: int,
    month: int,
    timesheet: TimesheetUpdate,
) -> Dict:
    """
    Update a timesheet.
    
    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet
        timesheet: Updated timesheet data
        
    Returns:
        Updated timesheet record
        
    Raises:
        HTTPException: If employee or timesheet not found
    """
    # Verify employee exists
    await get_employee(conn, employee_uuid)
    
    # Verify timesheet exists
    await get_employee_timesheet(conn, employee_uuid, year, month)
    
    # Update timesheet
    updated_timesheet = await timesheet_repository.update_timesheet(
        conn, employee_uuid, year, month, timesheet
    )
    
    if not updated_timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timesheet for employee {employee_uuid}, year {year}, month {month} not found"
        )
    
    return updated_timesheet


async def delete_employee_timesheet(
    conn: aiosqlite.Connection, employee_uuid: UUID, year: int, month: int
) -> None:
    """
    Delete a timesheet.
    
    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet
        
    Raises:
        HTTPException: If employee or timesheet not found
    """
    # Verify employee exists
    await get_employee(conn, employee_uuid)
    
    # Verify timesheet exists
    await get_employee_timesheet(conn, employee_uuid, year, month)
    
    # Delete timesheet
    deleted = await timesheet_repository.delete_timesheet(conn, employee_uuid, year, month)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timesheet for employee {employee_uuid}, year {year}, month {month} not found"
        ) 