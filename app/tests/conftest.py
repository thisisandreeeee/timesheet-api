import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)


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
    return str(uuid.uuid4())


@pytest.fixture
def mock_employee_data():
    """Sample employee data."""
    return {"staff_code": "EMP001", "name": "John Doe"}


@pytest.fixture
def mock_timesheet_data():
    """Sample timesheet data."""
    return {
        "year": 2025,
        "month": 6,
        "total_working_days": 22,
        "total_ot_hours": 5.5,
        "total_sundays_worked": 2,
        "total_ot_hours_on_sundays": 1.0,
    }


@pytest.fixture
def override_get_db(mock_db_conn):
    """Override the get_db dependency."""
    app.dependency_overrides[get_db] = lambda: mock_db_conn
    yield
    app.dependency_overrides = {}
