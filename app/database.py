import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite
from fastapi import Depends

DATABASE_URL = "sqlite:///./timesheet.db"
DATABASE_FILE = "./timesheet.db"

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Create and yield a database connection.
    """
    conn = await aiosqlite.connect(DATABASE_FILE)
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
    finally:
        await conn.close()

@asynccontextmanager
async def lifespan(app):
    """
    Lifecycle manager for the application.
    Creates database tables if they don't exist.
    """
    # Create tables on startup
    async with aiosqlite.connect(DATABASE_FILE) as conn:
        # Create Employee table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                uuid TEXT PRIMARY KEY,
                staff_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
            """
        )
        
        # Create Timesheet table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_uuid TEXT NOT NULL,
                year INTEGER NOT NULL CHECK (year BETWEEN 2000 AND 2100),
                month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
                total_working_days INTEGER NOT NULL CHECK (total_working_days >= 0),
                total_ot_hours REAL NOT NULL CHECK (total_ot_hours >= 0),
                total_sundays_worked INTEGER NOT NULL CHECK (total_sundays_worked >= 0),
                total_ot_hours_on_sundays REAL NOT NULL CHECK (total_ot_hours_on_sundays >= 0),
                FOREIGN KEY (employee_uuid) REFERENCES employees (uuid) ON DELETE CASCADE,
                UNIQUE (employee_uuid, year, month)
            )
            """
        )
        
        await conn.commit()
    
    yield
    
    # No cleanup needed for SQLite 