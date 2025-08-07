"""
Pytest configuration and fixtures for Medical Records application tests.
"""
import asyncio
import os
import tempfile
from datetime import date
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db, Base
from app.main import app
from app.api import deps
from app.models.models import User, Patient
from app.crud.user import user as user_crud
from app.crud.patient import patient as patient_crud
from app.schemas.user import UserCreate
from app.schemas.patient import PatientCreate
from app.core.security import create_access_token
from tests.utils.user import create_random_user, create_user_authentication_headers


# Test database setup
@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using PostgreSQL from Docker stack."""
    # Use PostgreSQL from Docker stack (port 5433 as configured in docker-compose.yml)
    SQLALCHEMY_DATABASE_URL = "postgresql://medapp:your_secure_database_password_here@localhost:5433/medical_records"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
        full_name="Test User",
        role="user"
    )
    user = user_crud.create(db_session, obj_in=user_data)
    
# Don't create patient automatically - let tests create as needed
    
    return user


@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> User:
    """Create a test admin user."""
    user_data = UserCreate(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
        full_name="Admin User",
        role="admin"
    )
    return user_crud.create(db_session, obj_in=user_data)


@pytest.fixture(scope="function")
def test_patient(db_session: Session, test_user: User) -> Patient:
    """Create a patient record for the test user."""
    patient_data = PatientCreate(
        first_name="Test",
        last_name="User",
        birth_date="1990-01-01",
        gender="M",
        address="123 Test St"
    )
    return patient_crud.create_for_user(
        db_session,
        user_id=test_user.id,
        patient_data=patient_data
    )


@pytest.fixture(scope="function")
def user_token_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_token_headers(test_admin_user: User) -> dict[str, str]:
    """Create authentication headers for admin user."""
    access_token = create_access_token(data={"sub": test_admin_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, user_token_headers: dict) -> TestClient:
    """Test client with authentication headers pre-configured."""
    client.headers.update(user_token_headers)
    return client


@pytest.fixture(scope="function")
def admin_client(client: TestClient, admin_token_headers: dict) -> TestClient:
    """Test client with admin authentication headers pre-configured."""
    client.headers.update(admin_token_headers)
    return client


# Async fixtures for async tests
@pytest_asyncio.fixture
async def async_db_session(test_db_engine) -> AsyncGenerator[Session, None]:
    """Create an async database session for testing."""
    # Note: This is a simplified version. In a real async setup,
    # you would use async SQLAlchemy
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# Test data fixtures
@pytest.fixture
def sample_medication_data():
    """Sample medication data for testing."""
    return {
        "name": "Test Medication",
        "dosage": "10mg",
        "frequency": "Daily",
        "start_date": "2023-01-01",
        "end_date": None,
        "prescribing_doctor": "Dr. Test",
        "notes": "Test medication notes",
        "status": "active"
    }


@pytest.fixture
def sample_lab_result_data():
    """Sample lab result data for testing."""
    return {
        "test_name": "Complete Blood Count",
        "test_date": "2023-06-15",
        "result": "Normal",
        "reference_range": "Within normal limits",
        "ordering_doctor": "Dr. Test",
        "lab_name": "Test Lab",
        "notes": "All values normal",
        "status": "completed"
    }


@pytest.fixture
def sample_practitioner_data():
    """Sample practitioner data for testing."""
    return {
        "name": "Dr. Test Smith",
        "specialty": "Family Medicine",
        "phone_number": "555-0123",
        "email": "dr.test@example.com",
        "address": "123 Medical Center Dr",
        "website": "https://drtest.com",
        "rating": 4.5,
        "status": "active"
    }


@pytest.fixture
def sample_vitals_data():
    """Sample vitals data for testing."""
    return {
        "measurement_date": "2023-12-01",
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "heart_rate": 72,
        "temperature": 98.6,
        "weight": 180,
        "height": 70,
        "bmi": 25.8,
        "notes": "Normal vitals"
    }


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "postgresql://medapp:your_secure_database_password_here@localhost:5433/medical_records"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise in tests
    os.environ["SKIP_MIGRATIONS"] = "true"  # Skip database migrations in tests
    
    yield
    
    # Cleanup
    test_env_vars = ["TESTING", "DATABASE_URL", "SECRET_KEY", "LOG_LEVEL", "SKIP_MIGRATIONS"]
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]


# File handling fixtures
@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for file uploads during testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_dir = getattr(settings, 'UPLOAD_DIR', None)
        settings.UPLOAD_DIR = temp_dir
        
        yield temp_dir
        
        if original_upload_dir:
            settings.UPLOAD_DIR = original_upload_dir


@pytest.fixture
def sample_test_file():
    """Create a sample test file for upload testing."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
        f.write("This is a test file for lab results.")
        f.flush()
        
        yield f.name
        
        # Cleanup
        try:
            os.unlink(f.name)
        except OSError:
            pass


# Mocking utilities
@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock email service for testing."""
    sent_emails = []
    
    def mock_send_email(to_email: str, subject: str, body: str):
        sent_emails.append({
            "to": to_email,
            "subject": subject,
            "body": body
        })
        return True
    
    # Mock the email service if it exists
    # monkeypatch.setattr("app.services.email.send_email", mock_send_email)
    
    return sent_emails


@pytest.fixture
def mock_file_storage(monkeypatch, temp_upload_dir):
    """Mock file storage operations for testing."""
    stored_files = {}
    
    def mock_store_file(file_content: bytes, filename: str) -> str:
        file_path = os.path.join(temp_upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        stored_files[filename] = file_path
        return file_path
    
    def mock_delete_file(filename: str) -> bool:
        file_path = stored_files.get(filename)
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            del stored_files[filename]
            return True
        return False
    
    return {
        "store_file": mock_store_file,
        "delete_file": mock_delete_file,
        "stored_files": stored_files
    }


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Utility for measuring test performance."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.duration
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Cleanup utilities
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup after each test."""
    yield
    
    # Clear any global state
    # Reset singletons, clear caches, etc.
    pass