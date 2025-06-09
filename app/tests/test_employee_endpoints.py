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
def mock_employee_data():
    """Sample employee data."""
    return {
        "staff_code": "EMP001",
        "name": "John Doe"
    }


@pytest.fixture
def mock_employee_uuid():
    """Mock employee UUID."""
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_create_employee_success(test_client, mock_employee_data, override_get_db):
    """Test successful employee creation."""
    # Mock the create_employee function
    with patch("app.routers.employee_routes.employee_service.create_employee") as mock_create:
        # Configure the mock to return sample employee with UUID
        employee_uuid = str(uuid.uuid4())
        mock_create.return_value = {
            "uuid": employee_uuid,
            "staff_code": mock_employee_data["staff_code"],
            "name": mock_employee_data["name"]
        }

        # Make the request
        response = test_client.post(
            "/employees",
            json=mock_employee_data
        )

        # Check response
        assert response.status_code == 201
        data = response.json()
        assert data["uuid"] == employee_uuid
        assert data["staff_code"] == mock_employee_data["staff_code"]
        assert data["name"] == mock_employee_data["name"]


@pytest.mark.asyncio
async def test_create_employee_duplicate(test_client, mock_employee_data, override_get_db):
    """Test employee creation with duplicate staff code."""
    # Mock the create_employee function to raise conflict error
    with patch("app.routers.employee_routes.employee_service.create_employee", 
               side_effect=HTTPException(status_code=409, detail="Employee with staff code 'EMP001' already exists")):
        # Make the request
        response = test_client.post(
            "/employees",
            json=mock_employee_data
        )

        # Check response
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_employees(test_client, override_get_db):
    """Test getting all employees."""
    # Mock the get_all_employees function
    with patch("app.routers.employee_routes.employee_service.get_all_employees") as mock_get_all:
        # Configure the mock to return sample employees
        mock_get_all.return_value = [
            {
                "uuid": str(uuid.uuid4()),
                "staff_code": "EMP001",
                "name": "John Doe"
            },
            {
                "uuid": str(uuid.uuid4()),
                "staff_code": "EMP002",
                "name": "Jane Smith"
            }
        ]

        # Make the request
        response = test_client.get("/employees")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["staff_code"] == "EMP001"
        assert data[1]["staff_code"] == "EMP002"


@pytest.mark.asyncio
async def test_get_employee_by_uuid(test_client, mock_employee_uuid, override_get_db):
    """Test getting a specific employee by UUID."""
    # Mock the get_employee function
    with patch("app.routers.employee_routes.employee_service.get_employee") as mock_get:
        # Configure the mock to return a sample employee
        mock_get.return_value = {
            "uuid": mock_employee_uuid,
            "staff_code": "EMP001",
            "name": "John Doe"
        }

        # Make the request
        response = test_client.get(f"/employees/{mock_employee_uuid}")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == mock_employee_uuid
        assert data["staff_code"] == "EMP001"
        assert data["name"] == "John Doe"


@pytest.mark.asyncio
async def test_get_employee_not_found(test_client, mock_employee_uuid, override_get_db):
    """Test getting a non-existent employee."""
    # Mock the get_employee function to raise not found error
    with patch("app.routers.employee_routes.employee_service.get_employee", 
               side_effect=HTTPException(status_code=404, detail="Employee not found")):
        # Make the request
        response = test_client.get(f"/employees/{mock_employee_uuid}")

        # Check response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_employee(test_client, mock_employee_uuid, override_get_db):
    """Test updating an employee."""
    # Mock the update_employee function
    with patch("app.routers.employee_routes.employee_service.update_employee") as mock_update:
        # Configure the mock to return updated employee
        mock_update.return_value = {
            "uuid": mock_employee_uuid,
            "staff_code": "EMP001-UPDATED",
            "name": "John Doe Updated"
        }

        # Make the request
        update_data = {
            "staff_code": "EMP001-UPDATED",
            "name": "John Doe Updated"
        }
        response = test_client.put(
            f"/employees/{mock_employee_uuid}",
            json=update_data
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == mock_employee_uuid
        assert data["staff_code"] == "EMP001-UPDATED"
        assert data["name"] == "John Doe Updated"


@pytest.mark.asyncio
async def test_delete_employee(test_client, mock_employee_uuid, override_get_db):
    """Test deleting an employee."""
    # Mock the delete_employee function
    with patch("app.routers.employee_routes.employee_service.delete_employee") as mock_delete:
        # Make the request
        response = test_client.delete(f"/employees/{mock_employee_uuid}")

        # Check response
        assert response.status_code == 204
        assert response.content == b''  # No content
        # Check that the mock was called with the correct parameters
        mock_delete.assert_called_once() 