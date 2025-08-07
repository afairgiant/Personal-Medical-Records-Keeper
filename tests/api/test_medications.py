"""
Tests for Medication API endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.schemas.patient import PatientCreate
from tests.utils.user import create_random_user, create_token_headers_for_user


class TestMedicationAPI:
    """Test Medication API endpoints."""

    @pytest.fixture
    def user_with_patient(self, db_session: Session):
        """Create a user with patient record for testing."""
        user_data = create_random_user(db_session)
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date="1990-01-01",
            gender="M",
            address="123 Main St"
        )
        patient = patient_crud.create_for_user(
            db_session, user_id=user_data["user"].id, patient_data=patient_data
        )
        return {**user_data, "patient": patient}

    @pytest.fixture
    def authenticated_headers(self, user_with_patient):
        """Create authentication headers."""
        return create_token_headers_for_user(user_with_patient["user"])

    def test_create_medication_success(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test successful medication creation."""
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "route": "oral",
            "effective_period_start": "2024-01-01",
            "status": "active",
            "indication": "Pain relief"
        }

        response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["medication_name"] == "Aspirin"
        assert data["dosage"] == "100mg"
        assert data["frequency"] == "once daily"
        assert data["route"] == "oral"
        assert data["status"] == "active"
        assert data["patient_id"] == user_with_patient["patient"].id

    def test_create_medication_unauthorized(self, client: TestClient):
        """Test medication creation without authentication."""
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily"
        }

        response = client.post("/api/v1/medications/", json=medication_data)
        assert response.status_code == 401

    def test_create_medication_invalid_data(self, client: TestClient, authenticated_headers):
        """Test medication creation with invalid data."""
        medication_data = {
            "dosage": "100mg",  # Missing required medication_name
            "frequency": "once daily"
        }

        response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

    def test_get_medications_list(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting list of medications."""
        # First create a medication
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "route": "oral",
            "status": "active"
        }

        client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        # Get medications list
        response = client.get("/api/v1/medications/", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["medication_name"] == "Aspirin"

    def test_get_medication_by_id(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting a specific medication by ID."""
        # Create medication
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "route": "oral",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        medication_id = create_response.json()["id"]

        # Get medication by ID
        response = client.get(
            f"/api/v1/medications/{medication_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == medication_id
        assert data["medication_name"] == "Aspirin"

    def test_get_medication_nonexistent(self, client: TestClient, authenticated_headers):
        """Test getting a non-existent medication."""
        response = client.get("/api/v1/medications/99999", headers=authenticated_headers)
        assert response.status_code == 404

    def test_update_medication(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test updating a medication."""
        # Create medication
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "route": "oral",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        medication_id = create_response.json()["id"]

        # Update medication
        update_data = {
            "dosage": "200mg",
            "frequency": "twice daily",
            "indication": "Updated dosage per doctor"
        }

        response = client.put(
            f"/api/v1/medications/{medication_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dosage"] == "200mg"
        assert data["frequency"] == "twice daily"
        assert data["indication"] == "Updated dosage per doctor"
        assert data["medication_name"] == "Aspirin"  # Unchanged

    def test_delete_medication(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test deleting a medication."""
        # Create medication
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "route": "oral",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        medication_id = create_response.json()["id"]

        # Delete medication
        response = client.delete(
            f"/api/v1/medications/{medication_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/v1/medications/{medication_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    def test_medication_patient_isolation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own medications."""
        # Create first user with patient and medication
        user1_data = create_random_user(db_session)
        patient1_data = PatientCreate(
            first_name="User",
            last_name="One",
            birth_date="1990-01-01",
            gender="M"
        )
        patient1 = patient_crud.create_for_user(
            db_session, user_id=user1_data["user"].id, patient_data=patient1_data
        )
        headers1 = create_token_headers_for_user(user1_data["user"])

        # Create second user with patient
        user2_data = create_random_user(db_session)
        patient2_data = PatientCreate(
            first_name="User",
            last_name="Two",
            birth_date="1990-01-01",
            gender="F"
        )
        patient2 = patient_crud.create_for_user(
            db_session, user_id=user2_data["user"].id, patient_data=patient2_data
        )
        headers2 = create_token_headers_for_user(user2_data["user"])

        # User1 creates a medication
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily"
        }

        create_response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=headers1
        )

        medication_id = create_response.json()["id"]

        # User2 tries to access User1's medication - should fail
        response = client.get(
            f"/api/v1/medications/{medication_id}",
            headers=headers2
        )
        assert response.status_code == 404

        # User2 tries to update User1's medication - should fail
        update_response = client.put(
            f"/api/v1/medications/{medication_id}",
            json={"dosage": "200mg"},
            headers=headers2
        )
        assert update_response.status_code == 404

    def test_medication_search_and_filtering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test medication search and filtering capabilities."""
        # Create multiple medications
        medications = [
            {
                "medication_name": "Aspirin",
                "dosage": "100mg",
                "status": "active",
                "indication": "Pain relief"
            },
            {
                "medication_name": "Ibuprofen",
                "dosage": "200mg",
                "status": "active",
                "indication": "Inflammation"
            },
            {
                "medication_name": "Acetaminophen",
                "dosage": "500mg",
                "status": "inactive",
                "indication": "Fever reduction"
            }
        ]

        for med_data in medications:
            client.post(
                "/api/v1/medications/",
                json=med_data,
                headers=authenticated_headers
            )

        # Test filtering by status
        response = client.get(
            "/api/v1/medications/?status=active",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(med["status"] == "active" for med in data)

        # Test search by medication name
        response = client.get(
            "/api/v1/medications/?search=Aspirin",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["medication_name"] == "Aspirin"

    def test_medication_pagination(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test medication pagination."""
        # Create multiple medications
        for i in range(5):
            medication_data = {
                "medication_name": f"Medication_{i}",
                "dosage": "100mg",
                "status": "active"
            }
            client.post(
                "/api/v1/medications/",
                json=medication_data,
                headers=authenticated_headers
            )

        # Test pagination
        response = client.get(
            "/api/v1/medications/?skip=2&limit=2",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_medication_with_dates(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test medication creation and updates with date fields."""
        medication_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "once daily",
            "effective_period_start": "2024-01-01",
            "effective_period_end": "2024-12-31",
            "status": "active"
        }

        response = client.post(
            "/api/v1/medications/",
            json=medication_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["effective_period_start"] == "2024-01-01"
        assert data["effective_period_end"] == "2024-12-31"

    def test_medication_validation_errors(self, client: TestClient, authenticated_headers):
        """Test various validation error scenarios."""
        # Test with invalid status
        invalid_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "status": "invalid_status"
        }

        response = client.post(
            "/api/v1/medications/",
            json=invalid_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test with invalid date format
        invalid_date_data = {
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "effective_period_start": "invalid-date"
        }

        response = client.post(
            "/api/v1/medications/",
            json=invalid_date_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422