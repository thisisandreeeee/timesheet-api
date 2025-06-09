from typing import Dict, List, Optional, Tuple
from uuid import UUID

import aiosqlite

from app.schemas.timesheet import TimesheetCreate, TimesheetUpdate


async def get_timesheets_by_employee(
    conn: aiosqlite.Connection, employee_uuid: UUID
) -> List[Dict]:
    """
    Get all timesheets for an employee.

    Args:
        conn: Database connection
        employee_uuid: Employee UUID

    Returns:
        List of timesheet records
    """
    async with conn.execute(
        """
        SELECT id, employee_uuid, year, month, total_working_days, total_ot_hours,
               total_sundays_worked, total_ot_hours_on_sundays
        FROM timesheets
        WHERE employee_uuid = ?
        ORDER BY year DESC, month DESC
        """,
        (str(employee_uuid),),
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_timesheet(
    conn: aiosqlite.Connection, employee_uuid: UUID, year: int, month: int
) -> Optional[Dict]:
    """
    Get a specific timesheet.

    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet

    Returns:
        Timesheet record or None if not found
    """
    async with conn.execute(
        """
        SELECT id, employee_uuid, year, month, total_working_days, total_ot_hours,
               total_sundays_worked, total_ot_hours_on_sundays
        FROM timesheets
        WHERE employee_uuid = ? AND year = ? AND month = ?
        """,
        (str(employee_uuid), year, month),
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_timesheet(
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
    """
    cursor = await conn.execute(
        """
        INSERT INTO timesheets (
            employee_uuid, year, month, total_working_days, total_ot_hours,
            total_sundays_worked, total_ot_hours_on_sundays
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(employee_uuid),
            timesheet.year,
            timesheet.month,
            timesheet.total_working_days,
            timesheet.total_ot_hours,
            timesheet.total_sundays_worked,
            timesheet.total_ot_hours_on_sundays,
        ),
    )
    await conn.commit()

    # Get the inserted record
    return await get_timesheet(conn, employee_uuid, timesheet.year, timesheet.month)


async def update_timesheet(
    conn: aiosqlite.Connection,
    employee_uuid: UUID,
    year: int,
    month: int,
    timesheet: TimesheetUpdate,
) -> Optional[Dict]:
    """
    Update a timesheet.

    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet
        timesheet: Updated timesheet data

    Returns:
        Updated timesheet record or None if not found
    """
    # Get current timesheet data
    current_timesheet = await get_timesheet(conn, employee_uuid, year, month)
    if not current_timesheet:
        return None

    # Prepare update values
    updates = {}
    if timesheet.total_working_days is not None:
        updates["total_working_days"] = timesheet.total_working_days
    if timesheet.total_ot_hours is not None:
        updates["total_ot_hours"] = timesheet.total_ot_hours
    if timesheet.total_sundays_worked is not None:
        updates["total_sundays_worked"] = timesheet.total_sundays_worked
    if timesheet.total_ot_hours_on_sundays is not None:
        updates["total_ot_hours_on_sundays"] = timesheet.total_ot_hours_on_sundays

    if not updates:
        return current_timesheet

    # Build update query
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values())
    values.extend([str(employee_uuid), year, month])

    await conn.execute(
        f"""
        UPDATE timesheets
        SET {set_clause}
        WHERE employee_uuid = ? AND year = ? AND month = ?
        """,
        values,
    )
    await conn.commit()

    # Return updated timesheet
    return await get_timesheet(conn, employee_uuid, year, month)


async def delete_timesheet(
    conn: aiosqlite.Connection, employee_uuid: UUID, year: int, month: int
) -> bool:
    """
    Delete a timesheet.

    Args:
        conn: Database connection
        employee_uuid: Employee UUID
        year: Year of the timesheet
        month: Month of the timesheet

    Returns:
        True if timesheet was deleted, False if not found
    """
    cursor = await conn.execute(
        """
        DELETE FROM timesheets
        WHERE employee_uuid = ? AND year = ? AND month = ?
        """,
        (str(employee_uuid), year, month),
    )
    await conn.commit()

    return cursor.rowcount > 0
