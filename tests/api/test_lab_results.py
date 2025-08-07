"""
Tests for Lab Results API endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import io

from app.crud.patient import patient as patient_crud
from app.schemas.patient import PatientCreate
from tests.utils.user import create_random_user, create_user_token_headers


class TestLabResultsAPI:
    """Test Lab Results API endpoints."""

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

    def test_create_lab_result_success(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test successful lab result creation."""
        lab_result_data = {
            "test_name": "Complete Blood Count",
            "test_code": "CBC",
            "result_value": "Normal",
            "units": "cells/mcL",
            "reference_range": "4500-11000",
            "status": "final",
            "collected_date": "2024-01-01",
            "result_date": "2024-01-02",
            "ordering_provider": "Dr. Smith"
        }

        response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["test_name"] == "Complete Blood Count"
        assert data["test_code"] == "CBC"
        assert data["result_value"] == "Normal"
        assert data["status"] == "final"
        assert data["patient_id"] == user_with_patient["patient"].id

    def test_create_lab_result_with_file(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test lab result creation with file upload."""
        # Create the lab result first
        lab_result_data = {
            "test_name": "Blood Chemistry Panel",
            "test_code": "CHEM",
            "result_value": "See attached report",
            "status": "final",
            "collected_date": "2024-01-01",
            "result_date": "2024-01-02"
        }

        response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        lab_result_id = response.json()["id"]

        # Upload a file for the lab result
        test_file_content = b"This is a test lab result file content"
        test_file = io.BytesIO(test_file_content)

        files = {
            "file": ("test_lab_result.pdf", test_file, "application/pdf")
        }

        upload_response = client.post(
            f"/api/v1/lab-results/{lab_result_id}/files/",
            files=files,
            headers=authenticated_headers
        )

        assert upload_response.status_code == 201
        file_data = upload_response.json()
        assert file_data["original_filename"] == "test_lab_result.pdf"
        assert file_data["content_type"] == "application/pdf"
        assert file_data["lab_result_id"] == lab_result_id

    def test_get_lab_results_list(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting list of lab results."""
        # Create multiple lab results
        lab_results = [
            {
                "test_name": "Complete Blood Count",
                "test_code": "CBC",
                "result_value": "Normal",
                "status": "final",
                "collected_date": "2024-01-01"
            },
            {
                "test_name": "Lipid Panel",
                "test_code": "LIPID",
                "result_value": "Cholesterol: 180 mg/dL",
                "status": "final",
                "collected_date": "2024-01-15"
            }
        ]

        for lab_data in lab_results:
            client.post(
                "/api/v1/lab-results/",
                json=lab_data,
                headers=authenticated_headers
            )

        # Get lab results list
        response = client.get("/api/v1/lab-results/", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        
        # Should be ordered by date (most recent first)
        test_names = [result["test_name"] for result in data]
        assert "Complete Blood Count" in test_names
        assert "Lipid Panel" in test_names

    def test_get_lab_result_by_id(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting a specific lab result by ID."""
        lab_result_data = {
            "test_name": "Glucose Test",
            "test_code": "GLU",
            "result_value": "95 mg/dL",
            "units": "mg/dL",
            "reference_range": "70-100",
            "status": "final",
            "collected_date": "2024-01-01"
        }

        create_response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        lab_result_id = create_response.json()["id"]

        # Get lab result by ID
        response = client.get(
            f"/api/v1/lab-results/{lab_result_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lab_result_id
        assert data["test_name"] == "Glucose Test"
        assert data["result_value"] == "95 mg/dL"

    def test_update_lab_result(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test updating a lab result."""
        lab_result_data = {
            "test_name": "Hemoglobin A1C",
            "test_code": "HBA1C",
            "result_value": "6.2%",
            "status": "preliminary",
            "collected_date": "2024-01-01"
        }

        create_response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        lab_result_id = create_response.json()["id"]

        # Update the lab result
        update_data = {
            "result_value": "6.1%",
            "status": "final",
            "result_date": "2024-01-03",
            "notes": "Corrected value after re-analysis"
        }

        response = client.put(
            f"/api/v1/lab-results/{lab_result_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result_value"] == "6.1%"
        assert data["status"] == "final"
        assert data["result_date"] == "2024-01-03"
        assert data["notes"] == "Corrected value after re-analysis"

    def test_delete_lab_result(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test deleting a lab result."""
        lab_result_data = {
            "test_name": "Test to Delete",
            "test_code": "DEL",
            "result_value": "Delete me",
            "status": "final",
            "collected_date": "2024-01-01"
        }

        create_response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        lab_result_id = create_response.json()["id"]

        # Delete the lab result
        response = client.delete(
            f"/api/v1/lab-results/{lab_result_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/v1/lab-results/{lab_result_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    def test_lab_result_file_download(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test downloading lab result files."""
        # Create lab result
        lab_result_data = {
            "test_name": "X-Ray Results",
            "test_code": "XRAY",
            "result_value": "See attached image",
            "status": "final",
            "collected_date": "2024-01-01"
        }

        create_response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=authenticated_headers
        )

        lab_result_id = create_response.json()["id"]

        # Upload file
        test_file_content = b"This is test image data"
        test_file = io.BytesIO(test_file_content)

        files = {
            "file": ("xray.jpg", test_file, "image/jpeg")
        }

        upload_response = client.post(
            f"/api/v1/lab-results/{lab_result_id}/files/",
            files=files,
            headers=authenticated_headers
        )

        file_id = upload_response.json()["id"]

        # Download the file
        download_response = client.get(
            f"/api/v1/lab-result-files/{file_id}/download",
            headers=authenticated_headers
        )

        assert download_response.status_code == 200
        assert download_response.content == test_file_content

    def test_lab_result_search_and_filtering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test lab result search and filtering."""
        # Create lab results with different test codes and statuses
        lab_results = [
            {
                "test_name": "Complete Blood Count",
                "test_code": "CBC",
                "result_value": "Normal",
                "status": "final",
                "collected_date": "2024-01-01"
            },
            {
                "test_name": "Basic Metabolic Panel",
                "test_code": "BMP",
                "result_value": "Normal",
                "status": "preliminary",
                "collected_date": "2024-01-02"
            },
            {
                "test_name": "Complete Blood Count - Repeat",
                "test_code": "CBC",
                "result_value": "Improved",
                "status": "final",
                "collected_date": "2024-01-03"
            }
        ]

        for lab_data in lab_results:
            client.post(
                "/api/v1/lab-results/",
                json=lab_data,
                headers=authenticated_headers
            )

        # Test filtering by test code
        response = client.get(
            "/api/v1/lab-results/?test_code=CBC",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(result["test_code"] == "CBC" for result in data)

        # Test filtering by status
        response = client.get(
            "/api/v1/lab-results/?status=final",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(result["status"] == "final" for result in data)

        # Test search by test name
        response = client.get(
            "/api/v1/lab-results/?search=Blood Count",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_lab_result_date_range_filtering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test filtering lab results by date range."""
        # Create lab results across different dates
        lab_results = [
            {
                "test_name": "January Test",
                "test_code": "JAN",
                "collected_date": "2024-01-15",
                "status": "final"
            },
            {
                "test_name": "February Test",
                "test_code": "FEB",
                "collected_date": "2024-02-15",
                "status": "final"
            },
            {
                "test_name": "March Test",
                "test_code": "MAR",
                "collected_date": "2024-03-15",
                "status": "final"
            }
        ]

        for lab_data in lab_results:
            client.post(
                "/api/v1/lab-results/",
                json=lab_data,
                headers=authenticated_headers
            )

        # Filter by date range (January to February)
        response = client.get(
            "/api/v1/lab-results/?start_date=2024-01-01&end_date=2024-02-28",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        collected_dates = [result["collected_date"] for result in data]
        assert "2024-01-15" in collected_dates
        assert "2024-02-15" in collected_dates

    def test_lab_result_patient_isolation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own lab results."""
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

        # User1 creates a lab result
        lab_result_data = {
            "test_name": "Private Test",
            "test_code": "PRIV",
            "result_value": "Confidential",
            "status": "final",
            "collected_date": "2024-01-01"
        }

        create_response = client.post(
            "/api/v1/lab-results/",
            json=lab_result_data,
            headers=headers1
        )

        lab_result_id = create_response.json()["id"]

        # User2 tries to access User1's lab result - should fail
        response = client.get(
            f"/api/v1/lab-results/{lab_result_id}",
            headers=headers2
        )
        assert response.status_code == 404

    def test_lab_result_validation_errors(self, client: TestClient, authenticated_headers):
        """Test various validation error scenarios."""
        # Test missing required fields
        invalid_data = {
            "result_value": "Some value",
            "status": "final"
            # Missing test_name and test_code
        }

        response = client.post(
            "/api/v1/lab-results/",
            json=invalid_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid date format
        invalid_date_data = {
            "test_name": "Test",
            "test_code": "TEST",
            "collected_date": "invalid-date-format"
        }

        response = client.post(
            "/api/v1/lab-results/",
            json=invalid_date_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid status
        invalid_status_data = {
            "test_name": "Test",
            "test_code": "TEST",
            "status": "invalid_status"
        }

        response = client.post(
            "/api/v1/lab-results/",
            json=invalid_status_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422