from typing import Dict, List, Optional
from uuid import UUID, uuid4

import aiosqlite

from app.schemas.employee import EmployeeCreate, EmployeeUpdate


async def get_employees(conn: aiosqlite.Connection) -> List[Dict]:
    """
    Get all employees.

    Args:
        conn: Database connection

    Returns:
        List of employee records
    """
    async with conn.execute("SELECT uuid, staff_code, name FROM employees") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_employee_by_uuid(
    conn: aiosqlite.Connection, uuid: UUID
) -> Optional[Dict]:
    """
    Get employee by UUID.

    Args:
        conn: Database connection
        uuid: Employee UUID

    Returns:
        Employee record or None if not found
    """
    async with conn.execute(
        "SELECT uuid, staff_code, name FROM employees WHERE uuid = ?", (str(uuid),)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_employee_by_staff_code(
    conn: aiosqlite.Connection, staff_code: str
) -> Optional[Dict]:
    """
    Get employee by staff code.

    Args:
        conn: Database connection
        staff_code: Employee staff code

    Returns:
        Employee record or None if not found
    """
    async with conn.execute(
        "SELECT uuid, staff_code, name FROM employees WHERE staff_code = ?",
        (staff_code,),
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_employee(conn: aiosqlite.Connection, employee: EmployeeCreate) -> Dict:
    """
    Create a new employee.

    Args:
        conn: Database connection
        employee: Employee data

    Returns:
        Created employee record
    """
    employee_uuid = str(uuid4())

    await conn.execute(
        "INSERT INTO employees (uuid, staff_code, name) VALUES (?, ?, ?)",
        (employee_uuid, employee.staff_code, employee.name),
    )
    await conn.commit()

    return {
        "uuid": employee_uuid,
        "staff_code": employee.staff_code,
        "name": employee.name,
    }


async def update_employee(
    conn: aiosqlite.Connection, uuid: UUID, employee: EmployeeUpdate
) -> Optional[Dict]:
    """
    Update an employee.

    Args:
        conn: Database connection
        uuid: Employee UUID
        employee: Updated employee data

    Returns:
        Updated employee record or None if not found
    """
    # Get current employee data
    current_employee = await get_employee_by_uuid(conn, uuid)
    if not current_employee:
        return None

    # Prepare update values
    updates = {}
    if employee.staff_code is not None:
        updates["staff_code"] = employee.staff_code
    if employee.name is not None:
        updates["name"] = employee.name

    if not updates:
        return current_employee

    # Build update query
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values())
    values.append(str(uuid))

    await conn.execute(f"UPDATE employees SET {set_clause} WHERE uuid = ?", values)
    await conn.commit()

    # Return updated employee
    return await get_employee_by_uuid(conn, uuid)


async def delete_employee(conn: aiosqlite.Connection, uuid: UUID) -> bool:
    """
    Delete an employee.

    Args:
        conn: Database connection
        uuid: Employee UUID

    Returns:
        True if employee was deleted, False if not found
    """
    cursor = await conn.execute("DELETE FROM employees WHERE uuid = ?", (str(uuid),))
    await conn.commit()

    return cursor.rowcount > 0
