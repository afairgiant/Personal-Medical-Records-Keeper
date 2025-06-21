# Testing Documentation

This directory contains all tests for the Medical Records Management System.

## Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Python test runner script
├── run_tests.ps1           # PowerShell test runner script
├── test_auth.py            # Authentication tests
├── test_api.py             # General API tests
├── test_patients.py        # Patient-related tests
├── test_medical_records.py # Medical records tests
├── test_users.py           # User management tests
├── test_integration.py     # Integration tests
├── test_user_activity.py   # User activity tests
└── README.md               # This file
```

## Quick Start

### Running All Tests

**Python:**

```bash
python tests/run_tests.py all
```

**PowerShell:**

```powershell
.\tests\run_tests.ps1 all
```

**Direct pytest:**

```bash
python -m pytest tests/
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)

Tests for user registration, login, logout, and token management.

- User registration validation
- Login/logout functionality
- Token-based authentication
- Password security
- Role-based access

### 2. API Tests (`test_api.py`)

General API functionality tests.

- Health check endpoints
- CORS and middleware
- Error handling
- Security headers
- Performance basics

### 3. Patient Tests (`test_patients.py`)

Patient-specific functionality tests.

- Patient profile management
- Medical data access
- Patient data validation
- Patient-specific endpoints

### 4. Medical Records Tests (`test_medical_records.py`)

Tests for medical data management.

- Medication management
- Allergy tracking
- Vitals recording
- Lab results
- Conditions and diagnoses
- Immunizations

### 5. User Management Tests (`test_users.py`)

User profile and admin functionality tests.

- User profile updates
- Password changes
- Admin functionality
- Data export
- File uploads
- User validation

### 6. Integration Tests (`test_integration.py`)

End-to-end workflow tests.

- Complete user workflows
- Data consistency
- Error recovery
- Security workflows
- Performance scenarios

## Test Runner Options

### Available Test Types

| Command       | Description                           |
| ------------- | ------------------------------------- |
| `all`         | Run all tests                         |
| `unit`        | Run unit tests only                   |
| `integration` | Run integration tests only            |
| `auth`        | Run authentication tests              |
| `api`         | Run API tests                         |
| `patients`    | Run patient-related tests             |
| `medical`     | Run medical records tests             |
| `users`       | Run user management tests             |
| `security`    | Run security tests                    |
| `quick`       | Run quick tests (excludes slow tests) |
| `coverage`    | Run tests with coverage report        |
| `verbose`     | Run tests with verbose output         |
| `file <name>` | Run specific test file                |

### Examples

**Run authentication tests:**

```bash
python tests/run_tests.py auth
```

**Run with coverage:**

```bash
python tests/run_tests.py coverage
```

**Run specific test file:**

```bash
python tests/run_tests.py file patients
```

**PowerShell examples:**

```powershell
.\tests\run_tests.ps1 auth
.\tests\run_tests.ps1 coverage
.\tests\run_tests.ps1 file -TestFile patients
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

The pytest configuration includes:

- Test discovery patterns
- Markers for test categorization
- Output formatting
- Timeout settings
- Warning filters

### Test Fixtures (`conftest.py`)

Common fixtures available to all tests:

- `client`: Test client with database override
- `authenticated_user`: User with valid auth token
- `authenticated_admin`: Admin user with valid auth token
- `test_user_data`: Sample user data
- `sample_patient_data`: Sample patient data
- `sample_medication_data`: Sample medication data
- `sample_allergy_data`: Sample allergy data
- `sample_vitals_data`: Sample vitals data
- `sample_lab_result_data`: Sample lab result data

## Test Database

Tests use an in-memory SQLite database that is:

- Created fresh for each test session
- Isolated between tests
- Automatically cleaned up

## Coverage Reports

When running with coverage, reports are generated in:

- `htmlcov/` directory (HTML report)
- Terminal output (summary)

To view HTML coverage report:

```bash
# Run tests with coverage
python tests/run_tests.py coverage

# Open HTML report (Windows)
start htmlcov/index.html

# Open HTML report (macOS)
open htmlcov/index.html

# Open HTML report (Linux)
xdg-open htmlcov/index.html
```

## Test Markers

Tests can be marked with the following categories:

- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.auth` - Authentication-related tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.performance` - Performance tests

## Writing New Tests

### Test File Structure

```python
"""
Tests for [functionality description].
"""
from fastapi.testclient import TestClient


class Test[FeatureName]:
    """Test class for [feature] functionality."""

    def test_[specific_scenario](self, client: TestClient, authenticated_user):
        """Test [specific scenario description]."""
        headers = authenticated_user["headers"]

        response = client.get("/api/v1/endpoint", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Test both success and failure scenarios**
3. **Use appropriate fixtures** for setup
4. **Assert specific expected outcomes**
5. **Test edge cases and validation**
6. **Keep tests independent** and isolated
7. **Use appropriate markers** for categorization

### Adding New Fixtures

Add new fixtures to `conftest.py`:

```python
@pytest.fixture
def sample_new_data():
    """Sample data for testing new feature."""
    return {
        "field1": "value1",
        "field2": "value2"
    }
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the app directory is in Python path
2. **Database errors**: Check database connection and permissions
3. **Authentication errors**: Verify test user creation and token handling
4. **Dependency errors**: Install missing packages with `pip install -r requirements.txt`

### Debug Mode

Run tests with verbose output and no capture:

```bash
python -m pytest tests/ -v -s
```

### Running Individual Tests

```bash
# Run specific test class
python -m pytest tests/test_auth.py::TestAuthenticationEndpoints

# Run specific test method
python -m pytest tests/test_auth.py::TestAuthenticationEndpoints::test_login_success
```

## CI/CD Integration

For continuous integration, use:

```bash
# Basic test run
python -m pytest tests/

# With coverage and XML output for CI
python -m pytest tests/ --cov=app --cov-report=xml --junitxml=test-results.xml
```

## Dependencies

Required packages for testing:

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `fastapi` - For TestClient
- `sqlalchemy` - Database testing

Optional packages:

- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `pytest-mock` - Mocking utilities

Install all test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov
```
