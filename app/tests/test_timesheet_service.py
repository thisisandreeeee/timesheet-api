import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import timesheet_service
from app.schemas.timesheet import TimesheetCreate, TimesheetUpdate


@pytest.fixture
def mock_db_conn():
    """Mock database connection."""
    conn = AsyncMock()
    # Configure the mock to handle the dict conversion properly
    cursor_mock = AsyncMock()
    cursor_mock.fetchone.return_value = None
    conn.execute.return_value.__aenter__.return_value = cursor_mock
    return conn


@pytest.fixture
def mock_employee_uuid():
    """Mock employee UUID."""
    return uuid.uuid4()


@pytest.fixture
def mock_timesheet_data():
    """Sample timesheet data."""
    return {
        "id": 1,
        "employee_uuid": str(uuid.uuid4()),
        "year": 2025,
        "month": 6,
        "total_working_days": 22,
        "total_ot_hours": 5.5,
        "total_sundays_worked": 2,
        "total_ot_hours_on_sundays": 1.0
    }


@pytest.mark.asyncio
async def test_get_employee_timesheets(mock_db_conn, mock_employee_uuid):
    """Test getting all timesheets for an employee."""
    # Mock the repository functions directly
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheets_by_employee") as mock_get_timesheets
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        
        mock_timesheets = [
            {
                "id": 1,
                "employee_uuid": str(mock_employee_uuid),
                "year": 2025,
                "month": 5,
                "total_working_days": 21,
                "total_ot_hours": 4.5,
                "total_sundays_worked": 1,
                "total_ot_hours_on_sundays": 0.0
            },
            {
                "id": 2,
                "employee_uuid": str(mock_employee_uuid),
                "year": 2025,
                "month": 6,
                "total_working_days": 22,
                "total_ot_hours": 5.5,
                "total_sundays_worked": 2,
                "total_ot_hours_on_sundays": 1.0
            }
        ]
        mock_get_timesheets.return_value = mock_timesheets

        # Call the service function
        result = await timesheet_service.get_employee_timesheets(mock_db_conn, mock_employee_uuid)

        # Verify result
        assert result == mock_timesheets
        mock_get_employee_by_uuid.assert_called_once_with(mock_db_conn, mock_employee_uuid)
        mock_get_timesheets.assert_called_once_with(mock_db_conn, mock_employee_uuid)


@pytest.mark.asyncio
async def test_get_employee_timesheet_success(mock_db_conn, mock_employee_uuid, mock_timesheet_data):
    """Test getting a specific timesheet successfully."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = mock_timesheet_data

        # Call the service function
        year = mock_timesheet_data["year"]
        month = mock_timesheet_data["month"]
        result = await timesheet_service.get_employee_timesheet(mock_db_conn, mock_employee_uuid, year, month)

        # Verify result
        assert result == mock_timesheet_data
        mock_get_employee_by_uuid.assert_called_once_with(mock_db_conn, mock_employee_uuid)
        mock_get_timesheet.assert_called_once_with(mock_db_conn, mock_employee_uuid, year, month)


@pytest.mark.asyncio
async def test_get_employee_timesheet_not_found(mock_db_conn, mock_employee_uuid):
    """Test getting a non-existent timesheet."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = None

        # Call the service function and expect exception
        year, month = 2025, 6
        with pytest.raises(HTTPException) as excinfo:
            await timesheet_service.get_employee_timesheet(mock_db_conn, mock_employee_uuid, year, month)

        # Verify exception
        assert excinfo.value.status_code == 404
        assert "not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_create_employee_timesheet_success(mock_db_conn, mock_employee_uuid):
    """Test creating a timesheet successfully."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet,
        patch("app.repositories.timesheet_repository.create_timesheet") as mock_create
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = None  # No existing timesheet for this month
        
        created_timesheet = {
            "id": 1,
            "employee_uuid": str(mock_employee_uuid),
            "year": 2025,
            "month": 6,
            "total_working_days": 22,
            "total_ot_hours": 5.5,
            "total_sundays_worked": 2,
            "total_ot_hours_on_sundays": 1.0
        }
        mock_create.return_value = created_timesheet

        # Create timesheet data
        timesheet_data = TimesheetCreate(
            year=2025,
            month=6,
            total_working_days=22,
            total_ot_hours=5.5,
            total_sundays_worked=2,
            total_ot_hours_on_sundays=1.0
        )

        # Call the service function
        result = await timesheet_service.create_employee_timesheet(mock_db_conn, mock_employee_uuid, timesheet_data)

        # Verify result
        assert result == created_timesheet
        mock_get_employee_by_uuid.assert_called_once_with(mock_db_conn, mock_employee_uuid)
        mock_get_timesheet.assert_called_once_with(mock_db_conn, mock_employee_uuid, 2025, 6)
        mock_create.assert_called_once_with(mock_db_conn, mock_employee_uuid, timesheet_data)


@pytest.mark.asyncio
async def test_create_employee_timesheet_duplicate(mock_db_conn, mock_employee_uuid, mock_timesheet_data):
    """Test creating a timesheet that already exists."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = mock_timesheet_data  # Existing timesheet

        # Create timesheet data
        timesheet_data = TimesheetCreate(
            year=mock_timesheet_data["year"],
            month=mock_timesheet_data["month"],
            total_working_days=mock_timesheet_data["total_working_days"],
            total_ot_hours=mock_timesheet_data["total_ot_hours"],
            total_sundays_worked=mock_timesheet_data["total_sundays_worked"],
            total_ot_hours_on_sundays=mock_timesheet_data["total_ot_hours_on_sundays"]
        )

        # Call the service function and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await timesheet_service.create_employee_timesheet(mock_db_conn, mock_employee_uuid, timesheet_data)

        # Verify exception
        assert excinfo.value.status_code == 409
        assert "already exists" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_update_employee_timesheet_success(mock_db_conn, mock_employee_uuid, mock_timesheet_data):
    """Test updating a timesheet successfully."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet,
        patch("app.repositories.timesheet_repository.update_timesheet") as mock_update
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = mock_timesheet_data
        
        updated_timesheet = {
            "id": mock_timesheet_data["id"],
            "employee_uuid": str(mock_employee_uuid),
            "year": mock_timesheet_data["year"],
            "month": mock_timesheet_data["month"],
            "total_working_days": 23,  # Updated
            "total_ot_hours": 6.5,     # Updated
            "total_sundays_worked": mock_timesheet_data["total_sundays_worked"],
            "total_ot_hours_on_sundays": mock_timesheet_data["total_ot_hours_on_sundays"]
        }
        mock_update.return_value = updated_timesheet

        # Update data
        update_data = TimesheetUpdate(
            total_working_days=23,
            total_ot_hours=6.5
        )

        # Call the service function
        year = mock_timesheet_data["year"]
        month = mock_timesheet_data["month"]
        result = await timesheet_service.update_employee_timesheet(
            mock_db_conn, mock_employee_uuid, year, month, update_data
        )

        # Verify result
        assert result == updated_timesheet
        # The employee repository is called twice - once directly and once via get_employee_timesheet
        assert mock_get_employee_by_uuid.call_count == 2
        mock_get_timesheet.assert_called_once_with(mock_db_conn, mock_employee_uuid, year, month)
        mock_update.assert_called_once_with(mock_db_conn, mock_employee_uuid, year, month, update_data)


@pytest.mark.asyncio
async def test_delete_employee_timesheet_success(mock_db_conn, mock_employee_uuid, mock_timesheet_data):
    """Test deleting a timesheet successfully."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get_employee_by_uuid,
        patch("app.repositories.timesheet_repository.get_timesheet") as mock_get_timesheet,
        patch("app.repositories.timesheet_repository.delete_timesheet") as mock_delete
    ):
        # Set up mock return values
        mock_get_employee_by_uuid.return_value = {"uuid": str(mock_employee_uuid), "staff_code": "EMP001", "name": "John Doe"}
        mock_get_timesheet.return_value = mock_timesheet_data
        mock_delete.return_value = True

        # Call the service function
        year = mock_timesheet_data["year"]
        month = mock_timesheet_data["month"]
        await timesheet_service.delete_employee_timesheet(mock_db_conn, mock_employee_uuid, year, month)

        # Verify calls
        # The employee repository is called twice - once directly and once via get_employee_timesheet
        assert mock_get_employee_by_uuid.call_count == 2
        mock_get_timesheet.assert_called_once_with(mock_db_conn, mock_employee_uuid, year, month)
        mock_delete.assert_called_once_with(mock_db_conn, mock_employee_uuid, year, month) 