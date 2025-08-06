"""
Test vitals API endpoints.
"""
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.crud.practitioner import practitioner as practitioner_crud
from app.schemas.patient import PatientCreate
from app.schemas.practitioner import PractitionerCreate


class TestVitalsAPI:
    """Test vitals API endpoints."""

    @pytest.fixture
    def test_patient_with_practitioner(self, db_session: Session, test_user):
        """Create test patient and practitioner for vitals tests."""
        # Create practitioner
        practitioner_data = PractitionerCreate(
            name="Dr. Emily Chen",
            specialty="Family Medicine",
            practice="Community Health Center",
            phone_number="555-555-0123"
        )
        practitioner = practitioner_crud.create(db_session, obj_in=practitioner_data)
        
        # Create patient
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date=date(1990, 1, 1),
            gender="M",
            address="123 Main St"
        )
        patient = patient_crud.create_for_user(
            db_session, user_id=test_user.id, patient_data=patient_data
        )
        
        return {"patient": patient, "practitioner": practitioner}

    def test_create_vitals(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test creating new vitals record."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        vitals_data = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "temperature": 98.6,
            "weight": 180.0,
            "height": 70.0,
            "oxygen_saturation": 98.5,
            "respiratory_rate": 16,
            "blood_glucose": 85.0,
            "bmi": 25.8,
            "pain_scale": 2,
            "notes": "Normal vitals, patient feeling well",
            "location": "clinic",
            "device_used": "digital monitor"
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=vitals_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["systolic_bp"] == 120
        assert data["diastolic_bp"] == 80
        assert data["heart_rate"] == 72
        assert data["temperature"] == 98.6
        assert data["weight"] == 180.0
        assert data["patient_id"] == patient.id
        assert data["practitioner_id"] == practitioner.id

    def test_get_vitals_by_patient(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting vitals for a patient."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create test vitals
        vitals_data = [
            {
                "patient_id": patient.id,
                "practitioner_id": practitioner.id,
                "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "temperature": 98.6
            },
            {
                "patient_id": patient.id,
                "practitioner_id": practitioner.id,
                "recorded_date": datetime(2024, 1, 20, 14, 15, 0),
                "systolic_bp": 125,
                "diastolic_bp": 82,
                "heart_rate": 75,
                "temperature": 98.8
            }
        ]
        
        created_vitals = []
        for vital_data in vitals_data:
            response = authenticated_client.post("/api/v1/vitals/", json=vital_data)
            assert response.status_code == 201
            created_vitals.append(response.json())
        
        # Get vitals for patient
        response = authenticated_client.get(f"/api/v1/vitals/patient/{patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Should be ordered by recorded_date descending (most recent first)
        assert data[0]["systolic_bp"] == 125  # Most recent
        assert data[1]["systolic_bp"] == 120  # Earlier

    def test_get_recent_vitals(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting recent vitals within specified timeframe."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create recent and old vitals
        from datetime import datetime, timedelta
        
        recent_vitals = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "heart_rate": 70
        }
        
        old_vitals = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": (datetime.now() - timedelta(days=100)).isoformat(),
            "systolic_bp": 130,
            "diastolic_bp": 85,
            "heart_rate": 80
        }
        
        # Create both vitals
        response = authenticated_client.post("/api/v1/vitals/", json=recent_vitals)
        assert response.status_code == 201
        recent_vital = response.json()
        
        response = authenticated_client.post("/api/v1/vitals/", json=old_vitals)
        assert response.status_code == 201
        
        # Get recent vitals (last 30 days)
        response = authenticated_client.get(f"/api/v1/vitals/patient/{patient.id}/recent?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == recent_vital["id"]

    def test_update_vitals(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test updating vitals record."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create vitals
        vitals_data = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "notes": "Initial reading"
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=vitals_data)
        assert response.status_code == 201
        vitals = response.json()
        
        # Update vitals
        update_data = {
            "systolic_bp": 125,
            "diastolic_bp": 82,
            "notes": "Updated reading - slightly elevated",
            "pain_scale": 3
        }
        
        response = authenticated_client.put(f"/api/v1/vitals/{vitals['id']}", json=update_data)
        
        assert response.status_code == 200
        updated_vitals = response.json()
        assert updated_vitals["systolic_bp"] == 125
        assert updated_vitals["diastolic_bp"] == 82
        assert updated_vitals["notes"] == "Updated reading - slightly elevated"
        assert updated_vitals["pain_scale"] == 3
        assert updated_vitals["heart_rate"] == 72  # Unchanged

    def test_delete_vitals(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test deleting vitals record."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create vitals
        vitals_data = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": 120,
            "diastolic_bp": 80
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=vitals_data)
        assert response.status_code == 201
        vitals = response.json()
        
        # Delete vitals
        response = authenticated_client.delete(f"/api/v1/vitals/{vitals['id']}")
        
        assert response.status_code == 200
        
        # Verify vitals is deleted
        response = authenticated_client.get(f"/api/v1/vitals/{vitals['id']}")
        assert response.status_code == 404

    def test_get_vitals_by_id(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test getting specific vitals by ID."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create vitals
        vitals_data = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "temperature": 98.6,
            "bmi": 25.8
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=vitals_data)
        assert response.status_code == 201
        vitals = response.json()
        
        # Get vitals by ID
        response = authenticated_client.get(f"/api/v1/vitals/{vitals['id']}")
        
        assert response.status_code == 200
        retrieved_vitals = response.json()
        assert retrieved_vitals["systolic_bp"] == 120
        assert retrieved_vitals["diastolic_bp"] == 80
        assert retrieved_vitals["heart_rate"] == 72
        assert retrieved_vitals["bmi"] == 25.8

    def test_vitals_validation_errors(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test vitals validation errors."""
        patient = test_patient_with_practitioner["patient"]
        
        # Test missing required fields
        invalid_vitals = {
            "patient_id": patient.id,
            # Missing recorded_date (required field)
            "systolic_bp": 120
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=invalid_vitals)
        assert response.status_code == 422
        
        # Test invalid blood pressure values
        invalid_bp_vitals = {
            "patient_id": patient.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": -10,  # Invalid negative value
            "diastolic_bp": 300   # Unrealistic high value
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=invalid_bp_vitals)
        assert response.status_code == 422

    def test_bmi_calculation(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test BMI calculation in vitals."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create vitals with height and weight (BMI should be calculated)
        vitals_data = {
            "patient_id": patient.id,
            "practitioner_id": practitioner.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "weight": 180.0,  # pounds
            "height": 70.0,   # inches
            "bmi": 25.8       # Should match calculated BMI
        }
        
        response = authenticated_client.post("/api/v1/vitals/", json=vitals_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["weight"] == 180.0
        assert data["height"] == 70.0
        assert data["bmi"] == 25.8

    def test_vitals_search_and_filtering(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test searching and filtering vitals."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create vitals with different characteristics
        vitals_data = [
            {
                "patient_id": patient.id,
                "practitioner_id": practitioner.id,
                "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
                "systolic_bp": 140,  # High
                "diastolic_bp": 90,
                "location": "clinic"
            },
            {
                "patient_id": patient.id,
                "practitioner_id": practitioner.id,
                "recorded_date": datetime(2024, 1, 20, 14, 15, 0),
                "systolic_bp": 118,  # Normal
                "diastolic_bp": 78,
                "location": "home"
            }
        ]
        
        for vital_data in vitals_data:
            response = authenticated_client.post("/api/v1/vitals/", json=vital_data)
            assert response.status_code == 201
        
        # Filter by location
        response = authenticated_client.get(f"/api/v1/vitals/patient/{patient.id}?location=clinic")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["location"] == "clinic"
        assert data[0]["systolic_bp"] == 140

    def test_unauthorized_access(self, client: TestClient, test_patient_with_practitioner):
        """Test unauthorized access to vitals endpoints."""
        patient = test_patient_with_practitioner["patient"]
        
        # Test without authentication
        response = client.get(f"/api/v1/vitals/patient/{patient.id}")
        assert response.status_code == 401
        
        # Test creating vitals without auth
        vitals_data = {
            "patient_id": patient.id,
            "recorded_date": datetime(2024, 1, 15, 10, 30, 0),
            "systolic_bp": 120,
            "diastolic_bp": 80
        }
        
        response = client.post("/api/v1/vitals/", json=vitals_data)
        assert response.status_code == 401

    def test_vitals_trends_analysis(self, authenticated_client: TestClient, test_patient_with_practitioner):
        """Test vitals trends analysis endpoint."""
        patient = test_patient_with_practitioner["patient"]
        practitioner = test_patient_with_practitioner["practitioner"]
        
        # Create series of vitals showing trend
        from datetime import datetime, timedelta
        
        base_date = datetime.now() - timedelta(days=30)
        vitals_series = [
            {
                "patient_id": patient.id,
                "practitioner_id": practitioner.id,
                "recorded_date": (base_date + timedelta(days=i*10)).isoformat(),
                "systolic_bp": 120 + i*5,  # Increasing trend
                "diastolic_bp": 80 + i*2,
                "weight": 180 + i*2
            }
            for i in range(3)
        ]
        
        for vital_data in vitals_series:
            response = authenticated_client.post("/api/v1/vitals/", json=vital_data)
            assert response.status_code == 201
        
        # Get vitals trends
        response = authenticated_client.get(f"/api/v1/vitals/patient/{patient.id}/trends")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should show increasing trend in blood pressure and weight
        assert len(data) == 3
        assert data[0]["systolic_bp"] >= data[1]["systolic_bp"]  # Most recent should be highest