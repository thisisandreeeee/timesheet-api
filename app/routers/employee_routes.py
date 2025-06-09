from typing import List
from uuid import UUID

import aiosqlite
from fastapi import APIRouter, Depends, status

from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.schemas.errors import ConflictErrorResponse, NotFoundErrorResponse
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get(
    "",
    response_model=List[EmployeeResponse],
    summary="List all employees",
    description="Retrieve a list of all employees in the system.",
)
async def get_employees(conn: aiosqlite.Connection = Depends(get_db)):
    """Get all employees."""
    employees = await employee_service.get_all_employees(conn)
    return employees


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
    description="Add a new employee to the system with name and staff code.",
    responses={status.HTTP_409_CONFLICT: {"model": ConflictErrorResponse}},
)
async def create_employee(
    employee: EmployeeCreate, conn: aiosqlite.Connection = Depends(get_db)
):
    """Create a new employee."""
    return await employee_service.create_employee(conn, employee)


@router.get(
    "/{uuid}",
    response_model=EmployeeResponse,
    summary="Get employee details",
    description="Retrieve details for a specific employee by UUID.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def get_employee(uuid: UUID, conn: aiosqlite.Connection = Depends(get_db)):
    """Get a specific employee."""
    return await employee_service.get_employee(conn, uuid)


@router.put(
    "/{uuid}",
    response_model=EmployeeResponse,
    summary="Update employee details",
    description="Update details for a specific employee by UUID.",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ConflictErrorResponse},
    },
)
async def update_employee(
    uuid: UUID, employee: EmployeeUpdate, conn: aiosqlite.Connection = Depends(get_db)
):
    """Update a specific employee."""
    return await employee_service.update_employee(conn, uuid, employee)


@router.delete(
    "/{uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee",
    description="Delete a specific employee and all associated timesheets.",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundErrorResponse}},
)
async def delete_employee(uuid: UUID, conn: aiosqlite.Connection = Depends(get_db)):
    """Delete a specific employee."""
    await employee_service.delete_employee(conn, uuid)
    return None
