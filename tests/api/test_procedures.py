"""
Tests for Procedures API endpoints.
"""
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.schemas.patient import PatientCreate
from tests.utils.user import create_random_user, create_user_token_headers


class TestProceduresAPI:
    """Test Procedures API endpoints."""

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
        return create_user_token_headers(user_with_patient["user"].id)

    def test_create_procedure_success(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test successful procedure creation."""
        procedure_data = {
            "procedure_name": "Appendectomy",
            "procedure_code": "44970",
            "date": "2024-01-15",
            "status": "completed",
            "location": "Main Operating Room",
            "urgency": "urgent",
            "anesthesia_type": "general",
            "duration_minutes": 120,
            "notes": "Laparoscopic appendectomy performed successfully"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["procedure_name"] == "Appendectomy"
        assert data["procedure_code"] == "44970"
        assert data["status"] == "completed"
        assert data["urgency"] == "urgent"
        assert data["anesthesia_type"] == "general"
        assert data["duration_minutes"] == 120
        assert data["patient_id"] == user_with_patient["patient"].id

    def test_create_procedure_minimal_data(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test procedure creation with minimal required data."""
        procedure_data = {
            "procedure_name": "Blood Draw",
            "date": "2024-01-15",
            "status": "completed"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["procedure_name"] == "Blood Draw"
        assert data["date"] == "2024-01-15"
        assert data["status"] == "completed"

    def test_create_scheduled_procedure(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test creating a scheduled procedure."""
        procedure_data = {
            "procedure_name": "Colonoscopy",
            "procedure_code": "45378",
            "date": "2024-03-15",
            "status": "scheduled",
            "urgency": "routine",
            "anesthesia_type": "conscious_sedation",
            "location": "Endoscopy Suite",
            "pre_procedure_instructions": "Fast for 12 hours before procedure",
            "estimated_duration_minutes": 45
        }

        response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["anesthesia_type"] == "conscious_sedation"
        assert data["pre_procedure_instructions"] == "Fast for 12 hours before procedure"

    def test_get_procedures_list(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting list of procedures."""
        # Create multiple procedures
        procedures = [
            {
                "procedure_name": "X-Ray Chest",
                "date": "2024-01-10",
                "status": "completed"
            },
            {
                "procedure_name": "MRI Brain",
                "date": "2024-01-20",
                "status": "completed"
            },
            {
                "procedure_name": "CT Scan Abdomen",
                "date": "2024-02-15",
                "status": "scheduled"
            }
        ]

        for proc_data in procedures:
            client.post(
                "/api/v1/procedures/",
                json=proc_data,
                headers=authenticated_headers
            )

        # Get procedures list
        response = client.get("/api/v1/procedures/", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

        # Should be ordered by date (most recent first)
        procedure_names = [proc["procedure_name"] for proc in data]
        assert "X-Ray Chest" in procedure_names
        assert "MRI Brain" in procedure_names
        assert "CT Scan Abdomen" in procedure_names

    def test_get_procedure_by_id(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting a specific procedure by ID."""
        procedure_data = {
            "procedure_name": "Cardiac Catheterization",
            "procedure_code": "93458",
            "date": "2024-01-15",
            "status": "completed",
            "urgency": "urgent",
            "anesthesia_type": "local",
            "duration_minutes": 90
        }

        create_response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        procedure_id = create_response.json()["id"]

        # Get procedure by ID
        response = client.get(
            f"/api/v1/procedures/{procedure_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == procedure_id
        assert data["procedure_name"] == "Cardiac Catheterization"
        assert data["procedure_code"] == "93458"

    def test_update_procedure(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test updating a procedure."""
        # Create procedure
        procedure_data = {
            "procedure_name": "Knee Arthroscopy",
            "date": "2024-01-15",
            "status": "scheduled",
            "urgency": "routine"
        }

        create_response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        procedure_id = create_response.json()["id"]

        # Update procedure
        update_data = {
            "status": "completed",
            "anesthesia_type": "regional",
            "duration_minutes": 75,
            "notes": "Arthroscopic meniscus repair completed successfully",
            "post_procedure_instructions": "Keep leg elevated, ice for 20 minutes every 2 hours"
        }

        response = client.put(
            f"/api/v1/procedures/{procedure_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["anesthesia_type"] == "regional"
        assert data["duration_minutes"] == 75
        assert data["notes"] == "Arthroscopic meniscus repair completed successfully"
        assert data["procedure_name"] == "Knee Arthroscopy"  # Unchanged

    def test_delete_procedure(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test deleting a procedure."""
        procedure_data = {
            "procedure_name": "Test Procedure to Delete",
            "date": "2024-01-15",
            "status": "scheduled"
        }

        create_response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        procedure_id = create_response.json()["id"]

        # Delete procedure
        response = client.delete(
            f"/api/v1/procedures/{procedure_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/v1/procedures/{procedure_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    def test_procedure_search_and_filtering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test procedure search and filtering."""
        # Create procedures with different statuses and types
        procedures = [
            {
                "procedure_name": "Surgical Procedure A",
                "date": "2024-01-15",
                "status": "completed",
                "urgency": "urgent",
                "anesthesia_type": "general"
            },
            {
                "procedure_name": "Diagnostic Procedure B",
                "date": "2024-01-20",
                "status": "scheduled",
                "urgency": "routine",
                "anesthesia_type": "local"
            },
            {
                "procedure_name": "Surgical Procedure C",
                "date": "2024-02-01",
                "status": "completed",
                "urgency": "routine",
                "anesthesia_type": "general"
            }
        ]

        for proc_data in procedures:
            client.post(
                "/api/v1/procedures/",
                json=proc_data,
                headers=authenticated_headers
            )

        # Test filtering by status
        response = client.get(
            "/api/v1/procedures/?status=completed",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(proc["status"] == "completed" for proc in data)

        # Test filtering by urgency
        response = client.get(
            "/api/v1/procedures/?urgency=urgent",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["urgency"] == "urgent"

        # Test filtering by anesthesia type
        response = client.get(
            "/api/v1/procedures/?anesthesia_type=general",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(proc["anesthesia_type"] == "general" for proc in data)

        # Test search by procedure name
        response = client.get(
            "/api/v1/procedures/?search=Surgical",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_procedure_date_range_filtering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test filtering procedures by date range."""
        # Create procedures across different dates
        procedures = [
            {
                "procedure_name": "January Procedure",
                "date": "2024-01-15",
                "status": "completed"
            },
            {
                "procedure_name": "February Procedure",
                "date": "2024-02-15",
                "status": "completed"
            },
            {
                "procedure_name": "March Procedure",
                "date": "2024-03-15",
                "status": "scheduled"
            }
        ]

        for proc_data in procedures:
            client.post(
                "/api/v1/procedures/",
                json=proc_data,
                headers=authenticated_headers
            )

        # Filter by date range (January to February)
        response = client.get(
            "/api/v1/procedures/?start_date=2024-01-01&end_date=2024-02-28",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        procedure_dates = [proc["date"] for proc in data]
        assert "2024-01-15" in procedure_dates
        assert "2024-02-15" in procedure_dates

    def test_procedure_anesthesia_tracking(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test anesthesia-specific fields and tracking."""
        procedure_data = {
            "procedure_name": "Major Surgery",
            "date": "2024-01-15",
            "status": "completed",
            "anesthesia_type": "general",
            "anesthesia_start_time": "2024-01-15T08:00:00",
            "anesthesia_end_time": "2024-01-15T10:30:00",
            "anesthesiologist": "Dr. Anesthesia",
            "pre_anesthesia_assessment": "ASA Class II, no complications expected",
            "post_anesthesia_notes": "Smooth recovery, no complications"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["anesthesia_type"] == "general"
        assert data["anesthesiologist"] == "Dr. Anesthesia"
        assert data["pre_anesthesia_assessment"] == "ASA Class II, no complications expected"
        assert data["post_anesthesia_notes"] == "Smooth recovery, no complications"

    def test_procedure_patient_isolation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own procedures."""
        # Create two users with patients
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
        headers1 = create_user_token_headers(user1_data["user"].id)

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
        headers2 = create_user_token_headers(user2_data["user"].id)

        # User1 creates a procedure
        procedure_data = {
            "procedure_name": "Private Surgery",
            "date": "2024-01-15",
            "status": "completed"
        }

        create_response = client.post(
            "/api/v1/procedures/",
            json=procedure_data,
            headers=headers1
        )

        procedure_id = create_response.json()["id"]

        # User2 tries to access User1's procedure - should fail
        response = client.get(
            f"/api/v1/procedures/{procedure_id}",
            headers=headers2
        )
        assert response.status_code == 404

    def test_procedure_validation_errors(self, client: TestClient, authenticated_headers):
        """Test various validation error scenarios."""
        # Test missing required fields
        invalid_data = {
            "status": "completed"
            # Missing procedure_name and date
        }

        response = client.post(
            "/api/v1/procedures/",
            json=invalid_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid status
        invalid_status_data = {
            "procedure_name": "Test",
            "date": "2024-01-15",
            "status": "invalid_status"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=invalid_status_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid urgency
        invalid_urgency_data = {
            "procedure_name": "Test",
            "date": "2024-01-15",
            "urgency": "invalid_urgency"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=invalid_urgency_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid anesthesia type
        invalid_anesthesia_data = {
            "procedure_name": "Test",
            "date": "2024-01-15",
            "anesthesia_type": "invalid_anesthesia"
        }

        response = client.post(
            "/api/v1/procedures/",
            json=invalid_anesthesia_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

    def test_procedure_scheduled_vs_completed(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test workflow from scheduled to completed procedure."""
        # Create scheduled procedure
        scheduled_data = {
            "procedure_name": "Outpatient Surgery",
            "date": "2024-03-15",
            "status": "scheduled",
            "urgency": "routine",
            "anesthesia_type": "local",
            "pre_procedure_instructions": "No food or drink after midnight"
        }

        create_response = client.post(
            "/api/v1/procedures/",
            json=scheduled_data,
            headers=authenticated_headers
        )

        procedure_id = create_response.json()["id"]

        # Update to completed with additional details
        completion_data = {
            "status": "completed",
            "duration_minutes": 45,
            "notes": "Procedure completed successfully",
            "post_procedure_instructions": "Rest for 24 hours, follow-up in 1 week",
            "complications": "None"
        }

        response = client.put(
            f"/api/v1/procedures/{procedure_id}",
            json=completion_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["duration_minutes"] == 45
        assert data["notes"] == "Procedure completed successfully"
        assert data["complications"] == "None"