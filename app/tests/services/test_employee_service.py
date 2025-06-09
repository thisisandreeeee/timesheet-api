import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services import employee_service
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


@pytest.fixture
def mock_db_conn():
    """Mock database connection."""
    return MagicMock()


@pytest.fixture
def mock_employee_data():
    """Sample employee data."""
    return {"uuid": str(uuid.uuid4()), "staff_code": "EMP001", "name": "John Doe"}


@pytest.mark.asyncio
async def test_get_all_employees(mock_db_conn):
    """Test getting all employees."""
    # Mock the repository function
    with patch("app.repositories.employee_repository.get_employees") as mock_get:
        # Set up mock return value
        mock_employees = [
            {"uuid": str(uuid.uuid4()), "staff_code": "EMP001", "name": "John Doe"},
            {"uuid": str(uuid.uuid4()), "staff_code": "EMP002", "name": "Jane Smith"},
        ]
        mock_get.return_value = mock_employees

        # Call the service function
        result = await employee_service.get_all_employees(mock_db_conn)

        # Verify result
        assert result == mock_employees
        mock_get.assert_called_once_with(mock_db_conn)


@pytest.mark.asyncio
async def test_get_employee_success(mock_db_conn, mock_employee_data):
    """Test getting an employee successfully."""
    # Mock the repository function
    with patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get:
        # Set up mock return value
        mock_get.return_value = mock_employee_data

        # Call the service function
        employee_uuid = uuid.UUID(mock_employee_data["uuid"])
        result = await employee_service.get_employee(mock_db_conn, employee_uuid)

        # Verify result
        assert result == mock_employee_data
        mock_get.assert_called_once_with(mock_db_conn, employee_uuid)


@pytest.mark.asyncio
async def test_get_employee_not_found(mock_db_conn):
    """Test getting a non-existent employee."""
    # Mock the repository function
    with patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get:
        # Set up mock return value
        mock_get.return_value = None

        # Call the service function and expect exception
        employee_uuid = uuid.uuid4()
        with pytest.raises(HTTPException) as excinfo:
            await employee_service.get_employee(mock_db_conn, employee_uuid)

        # Verify exception
        assert excinfo.value.status_code == 404
        assert f"Employee with UUID {employee_uuid} not found" in str(
            excinfo.value.detail
        )


@pytest.mark.asyncio
async def test_create_employee_success(mock_db_conn):
    """Test creating an employee successfully."""
    # Mock the repository functions
    with (
        patch(
            "app.repositories.employee_repository.get_employee_by_staff_code"
        ) as mock_get,
        patch("app.repositories.employee_repository.create_employee") as mock_create,
    ):
        # Set up mock return values
        mock_get.return_value = None  # No existing employee with same staff code

        created_employee = {
            "uuid": str(uuid.uuid4()),
            "staff_code": "EMP001",
            "name": "John Doe",
        }
        mock_create.return_value = created_employee

        # Create employee data
        employee_data = EmployeeCreate(staff_code="EMP001", name="John Doe")

        # Call the service function
        result = await employee_service.create_employee(mock_db_conn, employee_data)

        # Verify result
        assert result == created_employee
        mock_get.assert_called_once_with(mock_db_conn, "EMP001")
        mock_create.assert_called_once_with(mock_db_conn, employee_data)


@pytest.mark.asyncio
async def test_create_employee_duplicate(mock_db_conn):
    """Test creating an employee with duplicate staff code."""
    # Mock the repository function
    with patch(
        "app.repositories.employee_repository.get_employee_by_staff_code"
    ) as mock_get:
        # Set up mock return value - employee with same staff code exists
        existing_employee = {
            "uuid": str(uuid.uuid4()),
            "staff_code": "EMP001",
            "name": "Existing Employee",
        }
        mock_get.return_value = existing_employee

        # Create employee data
        employee_data = EmployeeCreate(staff_code="EMP001", name="John Doe")

        # Call the service function and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await employee_service.create_employee(mock_db_conn, employee_data)

        # Verify exception
        assert excinfo.value.status_code == 409
        assert "already exists" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_update_employee_success(mock_db_conn, mock_employee_data):
    """Test updating an employee successfully."""
    # Mock the repository functions
    with (
        patch(
            "app.repositories.employee_repository.get_employee_by_uuid"
        ) as mock_get_uuid,
        patch(
            "app.repositories.employee_repository.get_employee_by_staff_code"
        ) as mock_get_staff,
        patch("app.repositories.employee_repository.update_employee") as mock_update,
    ):
        # Set up mock return values
        mock_get_uuid.return_value = mock_employee_data
        mock_get_staff.return_value = None  # No other employee with same staff code

        updated_employee = {
            "uuid": mock_employee_data["uuid"],
            "staff_code": "EMP001-UPDATED",
            "name": "John Doe Updated",
        }
        mock_update.return_value = updated_employee

        # Update data
        employee_uuid = uuid.UUID(mock_employee_data["uuid"])
        update_data = EmployeeUpdate(
            staff_code="EMP001-UPDATED", name="John Doe Updated"
        )

        # Call the service function
        result = await employee_service.update_employee(
            mock_db_conn, employee_uuid, update_data
        )

        # Verify result
        assert result == updated_employee
        mock_get_uuid.assert_called_once_with(mock_db_conn, employee_uuid)
        mock_get_staff.assert_called_once_with(mock_db_conn, "EMP001-UPDATED")
        mock_update.assert_called_once_with(mock_db_conn, employee_uuid, update_data)


@pytest.mark.asyncio
async def test_update_employee_duplicate_staff_code(mock_db_conn, mock_employee_data):
    """Test updating an employee with a staff code that belongs to another employee."""
    # Mock the repository functions
    with (
        patch(
            "app.repositories.employee_repository.get_employee_by_uuid"
        ) as mock_get_uuid,
        patch(
            "app.repositories.employee_repository.get_employee_by_staff_code"
        ) as mock_get_staff,
    ):
        # Set up mock return values
        mock_get_uuid.return_value = mock_employee_data

        # Another employee with the staff code we want to use
        other_employee = {
            "uuid": str(uuid.uuid4()),  # Different UUID
            "staff_code": "EMP002",
            "name": "Other Employee",
        }
        mock_get_staff.return_value = other_employee

        # Update data with conflicting staff code
        employee_uuid = uuid.UUID(mock_employee_data["uuid"])
        update_data = EmployeeUpdate(
            staff_code="EMP002"
        )  # Already used by other employee

        # Call the service function and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await employee_service.update_employee(
                mock_db_conn, employee_uuid, update_data
            )

        # Verify exception
        assert excinfo.value.status_code == 409
        assert "already exists" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_delete_employee_success(mock_db_conn, mock_employee_data):
    """Test deleting an employee successfully."""
    # Mock the repository functions
    with (
        patch("app.repositories.employee_repository.get_employee_by_uuid") as mock_get,
        patch("app.repositories.employee_repository.delete_employee") as mock_delete,
    ):
        # Set up mock return values
        mock_get.return_value = mock_employee_data
        mock_delete.return_value = True  # Employee was deleted

        # Call the service function
        employee_uuid = uuid.UUID(mock_employee_data["uuid"])
        await employee_service.delete_employee(mock_db_conn, employee_uuid)

        # Verify calls
        mock_get.assert_called_once_with(mock_db_conn, employee_uuid)
        mock_delete.assert_called_once_with(mock_db_conn, employee_uuid)
