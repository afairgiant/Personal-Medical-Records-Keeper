"""
Test configuration and fixtures for the Medical Records Management System.
"""
# flake8: noqa: E402
# Imports below are ordered this way to set environment variables before app imports

import os
from pathlib import Path

# Set environment variables before importing any app modules
os.environ["SKIP_MIGRATIONS"] = "true"
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"

# Load test environment file if it exists
test_env_file = Path(__file__).parent / ".env.test"
if test_env_file.exists():
    with open(test_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base
from app.api import deps


# Create a test database
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a fresh database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[deps.get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "user"
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing."""
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "adminpassword123",
        "role": "admin"
    }


@pytest.fixture
def authenticated_user(client, db_session, test_user_data):
    """Create an authenticated user and return auth headers."""
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 200
    
    # Login user
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    return {
        "headers": headers,
        "user_data": test_user_data,
        "token": token
    }


@pytest.fixture
def authenticated_admin(client, db_session, test_admin_data):
    """Create an authenticated admin user and return auth headers."""
    # Register admin
    response = client.post("/api/v1/auth/register", json=test_admin_data)
    assert response.status_code == 200
    
    # Login admin
    login_data = {
        "username": test_admin_data["username"],
        "password": test_admin_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    return {
        "headers": headers,
        "user_data": test_admin_data,
        "token": token
    }


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
        "phone": "555-0123",
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_phone": "555-0124",
        "insurance_provider": "Test Insurance",
        "insurance_id": "TEST123456"
    }


@pytest.fixture
def sample_medication_data():
    """Sample medication data for testing."""
    return {
        "name": "Test Medication",
        "dosage": "10mg",
        "frequency": "Once daily",
        "start_date": "2024-01-01",
        "prescribing_doctor": "Dr. Test",
        "notes": "Test medication notes"
    }


@pytest.fixture
def sample_allergy_data():
    """Sample allergy data for testing."""
    return {
        "allergen": "Peanuts",
        "reaction": "Anaphylaxis",
        "severity": "severe",
        "notes": "Carries EpiPen"
    }


@pytest.fixture
def sample_vitals_data():
    """Sample vitals data for testing."""
    return {
        "systolic_pressure": 120,
        "diastolic_pressure": 80,
        "heart_rate": 70,
        "temperature": 98.6,
        "weight": 150.0,
        "height": 68.0,
        "notes": "Normal vitals"
    }


@pytest.fixture
def sample_lab_result_data():
    """Sample lab result data for testing."""
    return {
        "test_name": "Complete Blood Count",
        "test_date": "2024-01-01",
        "results": "Normal values",
        "reference_range": "WBC: 4.5-11.0",
        "status": "completed",
        "ordered_by": "Dr. Test",
        "notes": "Routine annual labs"
    }


@pytest.fixture
def cleanup_uploads():
    """Clean up uploaded files after tests."""
    yield
    # Clean up any test files that might have been created
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            if filename.startswith("test_"):
                os.remove(os.path.join(uploads_dir, filename))
