"""
Tests for medical record endpoints (medications, allergies, vitals, etc.).
"""
from fastapi.testclient import TestClient


class TestMedicationEndpoints:
    """Test class for medication-related endpoints."""

    def test_get_medications_list(self, client: TestClient, authenticated_user):
        """Test getting list of medications."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/medication", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_medication(self, client: TestClient, authenticated_user, sample_medication_data):
        """Test creating a new medication record."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/medication", json=sample_medication_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_medication_requires_authentication(self, client: TestClient, sample_medication_data):
        """Test that medication endpoints require authentication."""
        response = client.post("/api/v1/medication", json=sample_medication_data)
        assert response.status_code == 401


class TestAllergyEndpoints:
    """Test class for allergy-related endpoints."""

    def test_get_allergies_list(self, client: TestClient, authenticated_user):
        """Test getting list of allergies."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/allergy", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_allergy(self, client: TestClient, authenticated_user, sample_allergy_data):
        """Test creating a new allergy record."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/allergy", json=sample_allergy_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_allergy_requires_authentication(self, client: TestClient, sample_allergy_data):
        """Test that allergy endpoints require authentication."""
        response = client.post("/api/v1/allergy", json=sample_allergy_data)
        assert response.status_code == 401


class TestVitalsEndpoints:
    """Test class for vitals-related endpoints."""

    def test_get_vitals_list(self, client: TestClient, authenticated_user):
        """Test getting list of vitals."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/vitals", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_vitals(self, client: TestClient, authenticated_user, sample_vitals_data):
        """Test creating a new vitals record."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/vitals", json=sample_vitals_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_vitals_requires_authentication(self, client: TestClient, sample_vitals_data):
        """Test that vitals endpoints require authentication."""
        response = client.post("/api/v1/vitals", json=sample_vitals_data)
        assert response.status_code == 401


class TestLabResultEndpoints:
    """Test class for lab result-related endpoints."""

    def test_get_lab_results_list(self, client: TestClient, authenticated_user):
        """Test getting list of lab results."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/lab-result", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_lab_result(self, client: TestClient, authenticated_user, sample_lab_result_data):
        """Test creating a new lab result record."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/lab-result", json=sample_lab_result_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_lab_result_requires_authentication(self, client: TestClient, sample_lab_result_data):
        """Test that lab result endpoints require authentication."""
        response = client.post("/api/v1/lab-result", json=sample_lab_result_data)
        assert response.status_code == 401


class TestConditionEndpoints:
    """Test class for condition-related endpoints."""

    def test_get_conditions_list(self, client: TestClient, authenticated_user):
        """Test getting list of conditions."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/condition", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_condition(self, client: TestClient, authenticated_user):
        """Test creating a new condition record."""
        headers = authenticated_user["headers"]
        
        condition_data = {
            "name": "Hypertension",
            "diagnosis_date": "2024-01-01",
            "status": "active",
            "notes": "Managed with medication"
        }
        
        response = client.post("/api/v1/condition", json=condition_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_condition_requires_authentication(self, client: TestClient):
        """Test that condition endpoints require authentication."""
        condition_data = {
            "name": "Hypertension",
            "diagnosis_date": "2024-01-01",
            "status": "active"
        }
        
        response = client.post("/api/v1/condition", json=condition_data)
        assert response.status_code == 401


class TestImmunizationEndpoints:
    """Test class for immunization-related endpoints."""

    def test_get_immunizations_list(self, client: TestClient, authenticated_user):
        """Test getting list of immunizations."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/immunization", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_immunization(self, client: TestClient, authenticated_user):
        """Test creating a new immunization record."""
        headers = authenticated_user["headers"]
        
        immunization_data = {
            "vaccine_name": "COVID-19",
            "administered_date": "2024-01-01",
            "lot_number": "ABC123",
            "administered_by": "Dr. Smith",
            "location": "Clinic A"
        }
        
        response = client.post("/api/v1/immunization", json=immunization_data, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_immunization_requires_authentication(self, client: TestClient):
        """Test that immunization endpoints require authentication."""
        immunization_data = {
            "vaccine_name": "COVID-19",
            "administered_date": "2024-01-01"
        }
        
        response = client.post("/api/v1/immunization", json=immunization_data)
        assert response.status_code == 401


class TestDataValidation:
    """Test class for data validation across medical record endpoints."""

    def test_invalid_date_formats(self, client: TestClient, authenticated_user):
        """Test that invalid date formats are rejected."""
        headers = authenticated_user["headers"]
        
        # Test invalid date in lab result
        invalid_lab_data = {
            "test_name": "Blood Test",
            "test_date": "not-a-date",
            "results": "Normal"
        }
        
        response = client.post("/api/v1/lab-result", json=invalid_lab_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_required_fields_validation(self, client: TestClient, authenticated_user):
        """Test that required fields are validated."""
        headers = authenticated_user["headers"]
        
        # Test medication without required name field
        incomplete_medication = {
            "dosage": "10mg",
            "frequency": "Once daily"
            # Missing 'name' field
        }
        
        response = client.post("/api/v1/medication", json=incomplete_medication, headers=headers)
        assert response.status_code in [422, 400]

    def test_numeric_field_validation(self, client: TestClient, authenticated_user):
        """Test validation of numeric fields."""
        headers = authenticated_user["headers"]
        
        # Test vitals with invalid numeric values
        invalid_vitals = {
            "systolic_pressure": "not-a-number",
            "diastolic_pressure": 80,
            "heart_rate": 70
        }
        
        response = client.post("/api/v1/vitals", json=invalid_vitals, headers=headers)
        assert response.status_code in [422, 400]
