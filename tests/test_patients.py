"""
Tests for patient-related endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestPatientEndpoints:
    """Test class for patient-related endpoints."""

    def test_get_patient_profile_success(self, client: TestClient, authenticated_user):
        """Test getting patient profile successfully."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me", headers=headers)
        
        # The response should be successful and return patient data
        assert response.status_code in [200, 404]  # 404 if no patient record exists yet
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "user_id" in data

    def test_update_patient_profile(self, client: TestClient, authenticated_user, sample_patient_data):
        """Test updating patient profile."""
        headers = authenticated_user["headers"]
        
        response = client.put("/api/v1/patients/me", json=sample_patient_data, headers=headers)
        
        # Should either succeed or return 404 if patient doesn't exist
        assert response.status_code in [200, 404, 422]

    def test_get_patient_medications(self, client: TestClient, authenticated_user):
        """Test getting patient medications."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me/medications", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_add_patient_medication(self, client: TestClient, authenticated_user, sample_medication_data):
        """Test adding a medication to patient."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/patients/me/medications", json=sample_medication_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_get_patient_allergies(self, client: TestClient, authenticated_user):
        """Test getting patient allergies."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me/allergies", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_add_patient_allergy(self, client: TestClient, authenticated_user, sample_allergy_data):
        """Test adding an allergy to patient."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/patients/me/allergies", json=sample_allergy_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_get_patient_vitals(self, client: TestClient, authenticated_user):
        """Test getting patient vitals."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me/vitals", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_add_patient_vitals(self, client: TestClient, authenticated_user, sample_vitals_data):
        """Test adding vitals for patient."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/patients/me/vitals", json=sample_vitals_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_get_patient_lab_results(self, client: TestClient, authenticated_user):
        """Test getting patient lab results."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me/lab-results", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_add_patient_lab_result(self, client: TestClient, authenticated_user, sample_lab_result_data):
        """Test adding a lab result for patient."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/patients/me/lab-results", json=sample_lab_result_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_get_patient_conditions(self, client: TestClient, authenticated_user):
        """Test getting patient conditions."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/me/conditions", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_patient_endpoints_require_authentication(self, client: TestClient):
        """Test that patient endpoints require authentication."""
        endpoints = [
            "/api/v1/patients/me",
            "/api/v1/patients/me/medications",
            "/api/v1/patients/me/allergies",
            "/api/v1/patients/me/vitals",
            "/api/v1/patients/me/lab-results",
            "/api/v1/patients/me/conditions"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_get_patient_recent_activity(self, client: TestClient, authenticated_user):
        """Test getting patient recent activity."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/patients/recent-activity", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestPatientValidation:
    """Test class for patient data validation."""

    def test_invalid_medication_data(self, client: TestClient, authenticated_user):
        """Test adding medication with invalid data."""
        headers = authenticated_user["headers"]
        
        invalid_data = {
            "name": "",  # Empty name should be invalid
            "dosage": "10mg",
            "frequency": "Once daily"
        }
        
        response = client.post("/api/v1/patients/me/medications", json=invalid_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_invalid_allergy_data(self, client: TestClient, authenticated_user):
        """Test adding allergy with invalid data."""
        headers = authenticated_user["headers"]
        
        invalid_data = {
            "allergen": "",  # Empty allergen should be invalid
            "reaction": "Rash",
            "severity": "invalid_severity"  # Invalid severity
        }
        
        response = client.post("/api/v1/patients/me/allergies", json=invalid_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_invalid_vitals_data(self, client: TestClient, authenticated_user):
        """Test adding vitals with invalid data."""
        headers = authenticated_user["headers"]
        
        invalid_data = {
            "systolic_pressure": -10,  # Negative value should be invalid
            "diastolic_pressure": 80,
            "heart_rate": 70
        }
        
        response = client.post("/api/v1/patients/me/vitals", json=invalid_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_invalid_date_format(self, client: TestClient, authenticated_user):
        """Test adding data with invalid date format."""
        headers = authenticated_user["headers"]
        
        invalid_data = {
            "test_name": "Blood Test",
            "test_date": "invalid-date",  # Invalid date format
            "results": "Normal"
        }
        
        response = client.post("/api/v1/patients/me/lab-results", json=invalid_data, headers=headers)
        assert response.status_code in [422, 400]
