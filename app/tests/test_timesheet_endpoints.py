import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_employee_uuid():
    """Mock employee UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_timesheet_data():
    """Sample timesheet data."""
    return {
        "year": 2025,
        "month": 6,
        "total_working_days": 22,
        "total_ot_hours": 5.5,
        "total_sundays_worked": 2,
        "total_ot_hours_on_sundays": 1.0
    }


@pytest.mark.asyncio
async def test_create_timesheet_success(test_client, mock_employee_uuid, mock_timesheet_data, override_get_db):
    """Test successful timesheet creation."""
    # Mock the create_employee_timesheet function
    with patch("app.routers.timesheet_routes.timesheet_service.create_employee_timesheet") as mock_create:
        # Configure the mock to return sample timesheet with ID
        mock_create.return_value = {
            "id": 1,
            "employee_uuid": mock_employee_uuid,
            **mock_timesheet_data
        }

        # Make the request
        response = test_client.post(
            f"/employees/{mock_employee_uuid}/timesheets",
            json=mock_timesheet_data
        )

        # Check response
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["employee_uuid"] == mock_employee_uuid
        assert data["year"] == mock_timesheet_data["year"]
        assert data["month"] == mock_timesheet_data["month"]
        assert data["total_working_days"] == mock_timesheet_data["total_working_days"]
        assert data["total_ot_hours"] == mock_timesheet_data["total_ot_hours"]
        assert data["total_sundays_worked"] == mock_timesheet_data["total_sundays_worked"]
        assert data["total_ot_hours_on_sundays"] == mock_timesheet_data["total_ot_hours_on_sundays"]


@pytest.mark.asyncio
async def test_create_timesheet_duplicate(test_client, mock_employee_uuid, mock_timesheet_data, override_get_db):
    """Test timesheet creation with duplicate month/year."""
    # Mock the create_employee_timesheet function to raise conflict error
    with patch("app.routers.timesheet_routes.timesheet_service.create_employee_timesheet", 
               side_effect=HTTPException(status_code=409, detail="Timesheet for this month already exists")):
        # Make the request
        response = test_client.post(
            f"/employees/{mock_employee_uuid}/timesheets",
            json=mock_timesheet_data
        )

        # Check response
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_timesheet_invalid_data(test_client, mock_employee_uuid, override_get_db):
    """Test timesheet creation with invalid data."""
    # Invalid data: total_sundays_worked > total_working_days
    invalid_data = {
        "year": 2025,
        "month": 6,
        "total_working_days": 2,
        "total_ot_hours": 5.5,
        "total_sundays_worked": 5,  # More than working days
        "total_ot_hours_on_sundays": 1.0
    }

    # Make the request
    response = test_client.post(
        f"/employees/{mock_employee_uuid}/timesheets",
        json=invalid_data
    )

    # Check response
    assert response.status_code == 422
    response_json = response.json()
    # The response format is a list of validation errors
    assert "total_sundays_worked" in str(response_json)


@pytest.mark.asyncio
async def test_get_all_timesheets(test_client, mock_employee_uuid, override_get_db):
    """Test getting all timesheets for an employee."""
    # Mock the get_employee_timesheets function
    with patch("app.routers.timesheet_routes.timesheet_service.get_employee_timesheets") as mock_get_all:
        # Configure the mock to return sample timesheets
        mock_get_all.return_value = [
            {
                "id": 1,
                "employee_uuid": mock_employee_uuid,
                "year": 2025,
                "month": 5,
                "total_working_days": 21,
                "total_ot_hours": 4.5,
                "total_sundays_worked": 1,
                "total_ot_hours_on_sundays": 0.0
            },
            {
                "id": 2,
                "employee_uuid": mock_employee_uuid,
                "year": 2025,
                "month": 6,
                "total_working_days": 22,
                "total_ot_hours": 5.5,
                "total_sundays_worked": 2,
                "total_ot_hours_on_sundays": 1.0
            }
        ]

        # Make the request
        response = test_client.get(f"/employees/{mock_employee_uuid}/timesheets")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["month"] == 5
        assert data[1]["month"] == 6


@pytest.mark.asyncio
async def test_get_specific_timesheet(test_client, mock_employee_uuid, mock_timesheet_data, override_get_db):
    """Test getting a specific timesheet by year and month."""
    # Mock the get_employee_timesheet function
    with patch("app.routers.timesheet_routes.timesheet_service.get_employee_timesheet") as mock_get:
        # Configure the mock to return a sample timesheet
        mock_get.return_value = {
            "id": 1,
            "employee_uuid": mock_employee_uuid,
            **mock_timesheet_data
        }

        # Make the request
        year = mock_timesheet_data["year"]
        month = mock_timesheet_data["month"]
        response = test_client.get(f"/employees/{mock_employee_uuid}/timesheets/{year}/{month}")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["employee_uuid"] == mock_employee_uuid
        assert data["year"] == year
        assert data["month"] == month
        assert data["total_working_days"] == mock_timesheet_data["total_working_days"]


@pytest.mark.asyncio
async def test_get_timesheet_not_found(test_client, mock_employee_uuid, override_get_db):
    """Test getting a non-existent timesheet."""
    # Mock the get_employee_timesheet function to raise not found error
    with patch("app.routers.timesheet_routes.timesheet_service.get_employee_timesheet", 
               side_effect=HTTPException(status_code=404, detail="Timesheet not found")):
        # Make the request
        response = test_client.get(f"/employees/{mock_employee_uuid}/timesheets/2025/6")

        # Check response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_timesheet(test_client, mock_employee_uuid, override_get_db):
    """Test updating a timesheet."""
    # Mock the update_employee_timesheet function
    with patch("app.routers.timesheet_routes.timesheet_service.update_employee_timesheet") as mock_update:
        # Configure the mock to return updated timesheet
        updated_data = {
            "id": 1,
            "employee_uuid": mock_employee_uuid,
            "year": 2025,
            "month": 6,
            "total_working_days": 23,  # Updated
            "total_ot_hours": 6.5,     # Updated
            "total_sundays_worked": 2,
            "total_ot_hours_on_sundays": 1.0
        }
        mock_update.return_value = updated_data

        # Make the request with partial update
        update_data = {
            "total_working_days": 23,
            "total_ot_hours": 6.5
        }
        response = test_client.put(
            f"/employees/{mock_employee_uuid}/timesheets/2025/6",
            json=update_data
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["total_working_days"] == 23
        assert data["total_ot_hours"] == 6.5


@pytest.mark.asyncio
async def test_delete_timesheet(test_client, mock_employee_uuid, override_get_db):
    """Test deleting a timesheet."""
    # Mock the delete_employee_timesheet function
    with patch("app.routers.timesheet_routes.timesheet_service.delete_employee_timesheet") as mock_delete:
        # Make the request
        response = test_client.delete(f"/employees/{mock_employee_uuid}/timesheets/2025/6")

        # Check response
        assert response.status_code == 204
        assert response.content == b''  # No content
        # Check that the mock was called with the correct parameters
        mock_delete.assert_called_once() 