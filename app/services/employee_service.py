from typing import Dict, List, Optional
from uuid import UUID

import aiosqlite
from fastapi import HTTPException, status

from app.repositories import employee_repository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


async def get_all_employees(conn: aiosqlite.Connection) -> List[Dict]:
    """
    Get all employees.
    
    Args:
        conn: Database connection
        
    Returns:
        List of employee records
    """
    return await employee_repository.get_employees(conn)


async def get_employee(conn: aiosqlite.Connection, uuid: UUID) -> Dict:
    """
    Get employee by UUID.
    
    Args:
        conn: Database connection
        uuid: Employee UUID
        
    Returns:
        Employee record
        
    Raises:
        HTTPException: If employee not found
    """
    employee = await employee_repository.get_employee_by_uuid(conn, uuid)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with UUID {uuid} not found"
        )
    return employee


async def create_employee(conn: aiosqlite.Connection, employee: EmployeeCreate) -> Dict:
    """
    Create a new employee.
    
    Args:
        conn: Database connection
        employee: Employee data
        
    Returns:
        Created employee record
        
    Raises:
        HTTPException: If staff code already exists
    """
    # Check if staff code already exists
    existing_employee = await employee_repository.get_employee_by_staff_code(
        conn, employee.staff_code
    )
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with staff code '{employee.staff_code}' already exists"
        )
    
    return await employee_repository.create_employee(conn, employee)


async def update_employee(
    conn: aiosqlite.Connection, uuid: UUID, employee: EmployeeUpdate
) -> Dict:
    """
    Update an employee.
    
    Args:
        conn: Database connection
        uuid: Employee UUID
        employee: Updated employee data
        
    Returns:
        Updated employee record
        
    Raises:
        HTTPException: If employee not found or staff code already exists
    """
    # Check if employee exists
    await get_employee(conn, uuid)
    
    # Check if staff code is unique if provided
    if employee.staff_code is not None:
        existing_employee = await employee_repository.get_employee_by_staff_code(
            conn, employee.staff_code
        )
        if existing_employee and str(existing_employee["uuid"]) != str(uuid):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with staff code '{employee.staff_code}' already exists"
            )
    
    updated_employee = await employee_repository.update_employee(conn, uuid, employee)
    if not updated_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with UUID {uuid} not found"
        )
    
    return updated_employee


async def delete_employee(conn: aiosqlite.Connection, uuid: UUID) -> None:
    """
    Delete an employee.
    
    Args:
        conn: Database connection
        uuid: Employee UUID
        
    Raises:
        HTTPException: If employee not found
    """
    # Check if employee exists
    await get_employee(conn, uuid)
    
    deleted = await employee_repository.delete_employee(conn, uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with UUID {uuid} not found"
        ) 