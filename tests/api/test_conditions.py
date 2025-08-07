"""
Test condition API endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.crud.practitioner import practitioner as practitioner_crud
from app.schemas.patient import PatientCreate
from app.schemas.practitioner import PractitionerCreate


class TestConditionAPI:
    """Test condition API endpoints."""

    @pytest.fixture
    def test_patient_with_practitioner(self, db_session: Session, test_user):
        """Create test patient and practitioner."""
        # Create practitioner
        practitioner_data = PractitionerCreate(
            name="Dr. Sarah Johnson",
            specialty="Internal Medicine",
            practice="City Medical Center",
            phone_number="555-555-0123"
        )
        practitioner = practitioner_crud.create(db_session, obj_in=practitioner_data)
        
        # Create patient
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date="1990-01-01",
            gender="M",
            address="123 Main St"
        )
        patient = patient_crud.create_for_user(
            db_session, user_id=test_user.id, patient_data=patient_data
        )
        
        return {"patient": patient, "practitioner": practitioner}

    def test_create_condition(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test creating a new condition."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        condition_data = {
            "patient_id": patient.id,
            "diagnosis": "Essential Hypertension",
            "status": "active",
            "severity": "moderate",
            "onset_date": "2024-01-15",
            "icd10_code": "I10",
            "snomed_code": "38341003",
            "code_description": "Essential hypertension",
            "notes": "Patient has mild hypertension, monitoring required",
            "practitioner_id": practitioner.id
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["diagnosis"] == "Essential Hypertension"
        assert data["status"] == "active"
        assert data["severity"] == "moderate"
        assert data["patient_id"] == patient.id
        assert data["practitioner_id"] == practitioner.id

    def test_get_conditions_by_patient(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting conditions for a patient."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create test conditions
        conditions_data = [
            {
                "patient_id": patient.id,
                "diagnosis": "Diabetes Type 2",
                "status": "active",
                "severity": "mild",
                "practitioner_id": practitioner.id
            },
            {
                "patient_id": patient.id,
                "diagnosis": "Common Cold",
                "status": "resolved",
                "practitioner_id": practitioner.id
            }
        ]
        
        created_conditions = []
        for condition_data in conditions_data:
            response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
            assert response.status_code == 201
            created_conditions.append(response.json())
        
        # Get conditions for patient
        response = authenticated_client.get(f"/api/v1/conditions/patient/{patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify conditions
        diagnoses = {condition["diagnosis"] for condition in data}
        assert diagnoses == {"Diabetes Type 2", "Common Cold"}

    def test_get_active_conditions_only(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting only active conditions for a patient."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create active and resolved conditions
        conditions_data = [
            {
                "patient_id": patient.id,
                "diagnosis": "Active Condition",
                "status": "active",
                "practitioner_id": practitioner.id
            },
            {
                "patient_id": patient.id,
                "diagnosis": "Resolved Condition",
                "status": "resolved",
                "practitioner_id": practitioner.id
            }
        ]
        
        for condition_data in conditions_data:
            response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
            assert response.status_code == 201
        
        # Get active conditions only
        response = authenticated_client.get(f"/api/v1/conditions/patient/{patient.id}?status=active")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["diagnosis"] == "Active Condition"
        assert data[0]["status"] == "active"

    def test_update_condition(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test updating a condition."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create condition
        condition_data = {
            "patient_id": patient.id,
            "diagnosis": "Depression",
            "status": "active",
            "severity": "moderate",
            "practitioner_id": practitioner.id
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
        assert response.status_code == 201
        condition = response.json()
        
        # Update condition
        update_data = {
            "status": "inactive",
            "severity": "mild",
            "notes": "Patient responded well to treatment",
            "end_date": "2024-02-15"
        }
        
        response = authenticated_client.put(f"/api/v1/conditions/{condition['id']}", json=update_data)
        
        assert response.status_code == 200
        updated_condition = response.json()
        assert updated_condition["status"] == "inactive"
        assert updated_condition["severity"] == "mild"
        assert updated_condition["notes"] == "Patient responded well to treatment"
        assert updated_condition["end_date"] == "2024-02-15"
        assert updated_condition["diagnosis"] == "Depression"  # Unchanged

    def test_delete_condition(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test deleting a condition."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create condition
        condition_data = {
            "patient_id": patient.id,
            "diagnosis": "Seasonal Allergies",
            "status": "active",
            "practitioner_id": practitioner.id
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
        assert response.status_code == 201
        condition = response.json()
        
        # Delete condition
        response = authenticated_client.delete(f"/api/v1/conditions/{condition['id']}")
        
        assert response.status_code == 200
        
        # Verify condition is deleted
        response = authenticated_client.get(f"/api/v1/conditions/{condition['id']}")
        assert response.status_code == 404

    def test_get_condition_by_id(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting a specific condition by ID."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create condition
        condition_data = {
            "patient_id": patient.id,
            "diagnosis": "Chronic Kidney Disease",
            "status": "chronic",
            "severity": "moderate",
            "icd10_code": "N18.3",
            "practitioner_id": practitioner.id
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=condition_data)
        assert response.status_code == 201
        condition = response.json()
        
        # Get condition by ID
        response = authenticated_client.get(f"/api/v1/conditions/{condition['id']}")
        
        assert response.status_code == 200
        retrieved_condition = response.json()
        assert retrieved_condition["diagnosis"] == "Chronic Kidney Disease"
        assert retrieved_condition["status"] == "chronic"
        assert retrieved_condition["icd10_code"] == "N18.3"

    def test_condition_validation_errors(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test condition validation errors."""
        patient = test_patient_with_practitioner["patient"]
        
        # Test missing required fields
        invalid_condition = {
            "patient_id": patient.id,
            # Missing diagnosis (required field)
            "status": "active"
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=invalid_condition)
        assert response.status_code == 422
        
        # Test invalid status
        invalid_status_condition = {
            "patient_id": patient.id,
            "diagnosis": "Test Condition",
            "status": "invalid_status"
        }
        
        response = authenticated_client.post("/api/v1/conditions/", json=invalid_status_condition)
        assert response.status_code == 422

    def test_unauthorized_access(self, client: TestClient, test_patient_with_practitioner):
        """Test unauthorized access to condition endpoints."""
        patient = test_patient_with_practitioner["patient"]
        
        # Test without authentication
        response = client.get(f"/api/v1/conditions/patient/{patient.id}")
        assert response.status_code == 401
        
        # Test creating condition without auth
        condition_data = {
            "patient_id": patient.id,
            "diagnosis": "Test Condition",
            "status": "active"
        }
        
        response = client.post("/api/v1/conditions/", json=condition_data)
        assert response.status_code == 401