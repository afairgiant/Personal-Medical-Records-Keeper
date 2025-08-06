"""
Tests for Vitals CRUD operations.
"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from app.crud.vitals import vitals as vitals_crud
from app.crud.patient import patient as patient_crud
from app.models.models import Vitals
from app.schemas.vitals import VitalsCreate, VitalsUpdate
from app.schemas.patient import PatientCreate


class TestVitalsCRUD:
    """Test Vitals CRUD operations."""

    @pytest.fixture
    def test_patient(self, db_session: Session, test_user):
        """Create a test patient for vitals tests."""
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date=date(1990, 1, 1),
            gender="M",
            address="123 Main St"
        )
        return patient_crud.create_for_user(
            db_session, user_id=test_user.id, patient_data=patient_data
        )

    def test_create_vitals(self, db_session: Session, test_patient):
        """Test creating a vitals record."""
        vitals_data = VitalsCreate(
            patient_id=test_patient.id,
            recorded_date=datetime(2024, 1, 1, 10, 0, 0),
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            temperature=98.6,
            weight=150.0,
            height=68.0,
            oxygen_saturation=98
        )
        
        vital_signs = vitals_crud.create(db_session, obj_in=vitals_data)
        
        assert vital_signs is not None
        assert vital_signs.systolic_bp == 120
        assert vital_signs.diastolic_bp == 80
        assert vital_signs.heart_rate == 72
        assert vital_signs.temperature == 98.6
        assert vital_signs.weight == 150.0
        assert vital_signs.height == 68.0
        assert vital_signs.patient_id == test_patient.id

    def test_create_with_bmi(self, db_session: Session, test_patient):
        """Test creating vitals with automatic BMI calculation."""
        vitals_data = VitalsCreate(
            patient_id=test_patient.id,
            recorded_date=datetime(2024, 1, 1, 10, 0, 0),
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            temperature=98.6,
            weight=150.0,
            height=68.0
        )
        
        vital_signs = vitals_crud.create_with_bmi(db_session, obj_in=vitals_data)
        
        assert vital_signs is not None
        assert vital_signs.weight == 150.0
        assert vital_signs.height == 68.0
        assert vital_signs.bmi is not None
        # BMI = (150 / 68^2) * 703 ≈ 22.8
        assert abs(vital_signs.bmi - 22.8) < 0.1

    def test_calculate_bmi(self, db_session: Session):
        """Test BMI calculation."""
        # Test normal BMI calculation
        bmi = vitals_crud.calculate_bmi(weight_lbs=150.0, height_inches=68.0)
        assert abs(bmi - 22.8) < 0.1
        
        # Test different values
        bmi = vitals_crud.calculate_bmi(weight_lbs=200.0, height_inches=72.0)
        assert abs(bmi - 27.1) < 0.1
        
        # Test invalid values
        with pytest.raises(ValueError):
            vitals_crud.calculate_bmi(weight_lbs=0, height_inches=68.0)
        
        with pytest.raises(ValueError):
            vitals_crud.calculate_bmi(weight_lbs=150.0, height_inches=0)

    def test_get_latest_by_patient(self, db_session: Session, test_patient):
        """Test getting the latest vitals for a patient."""
        # Create multiple vitals records
        dates = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 10, 0, 0),
            datetime(2024, 1, 3, 10, 0, 0)
        ]
        
        created_vitals = []
        for i, date in enumerate(dates):
            vitals_data = VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=date,
                systolic_bp=120 + i,
                diastolic_bp=80 + i,
                heart_rate=72 + i,
                temperature=98.6
            )
            created_vitals.append(vitals_crud.create(db_session, obj_in=vitals_data))
        
        # Get latest vitals
        latest_vitals = vitals_crud.get_latest_by_patient(
            db_session, patient_id=test_patient.id
        )
        
        assert latest_vitals is not None
        assert latest_vitals.id == created_vitals[2].id  # Most recent
        assert latest_vitals.systolic_bp == 122

    def test_get_by_vital_type(self, db_session: Session, test_patient):
        """Test getting vitals by specific vital type."""
        # Create vitals with different measurements
        vitals_data = [
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 1, 10, 0, 0),
                systolic_bp=120,
                diastolic_bp=80,
                heart_rate=72
            ),
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 2, 10, 0, 0),
                temperature=98.6,
                weight=150.0
            ),
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 3, 10, 0, 0),
                systolic_bp=125,
                diastolic_bp=85,
                oxygen_saturation=98
            )
        ]
        
        for data in vitals_data:
            vitals_crud.create(db_session, obj_in=data)
        
        # Get blood pressure readings
        bp_readings = vitals_crud.get_by_vital_type(
            db_session, patient_id=test_patient.id, vital_type="blood_pressure"
        )
        
        assert len(bp_readings) == 2
        assert all(v.systolic_bp is not None for v in bp_readings)
        assert all(v.diastolic_bp is not None for v in bp_readings)

    def test_get_by_patient_date_range(self, db_session: Session, test_patient):
        """Test getting vitals within a date range."""
        # Create vitals across different dates
        dates = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 2, 1, 10, 0, 0),
            datetime(2024, 2, 15, 10, 0, 0)
        ]
        
        for i, date in enumerate(dates):
            vitals_data = VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=date,
                systolic_bp=120 + i,
                diastolic_bp=80 + i,
                heart_rate=72 + i
            )
            vitals_crud.create(db_session, obj_in=vitals_data)
        
        # Get vitals for January 2024
        january_vitals = vitals_crud.get_by_patient_date_range(
            db_session,
            patient_id=test_patient.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert len(january_vitals) == 2
        assert all(v.recorded_date.month == 1 for v in january_vitals)

    def test_get_vitals_stats(self, db_session: Session, test_patient):
        """Test getting vitals statistics."""
        # Create multiple vitals records
        vitals_data = [
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 1, 10, 0, 0),
                systolic_bp=120,
                diastolic_bp=80,
                heart_rate=72,
                temperature=98.6,
                weight=150.0,
                height=68.0
            ),
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 2, 10, 0, 0),
                systolic_bp=125,
                diastolic_bp=85,
                heart_rate=75,
                temperature=99.0,
                weight=152.0,
                height=68.0
            ),
            VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=datetime(2024, 1, 3, 10, 0, 0),
                systolic_bp=115,
                diastolic_bp=75,
                heart_rate=70,
                temperature=98.2,
                weight=151.0,
                height=68.0
            )
        ]
        
        for data in vitals_data:
            vitals_crud.create_with_bmi(db_session, obj_in=data)
        
        # Get statistics
        stats = vitals_crud.get_vitals_stats(db_session, patient_id=test_patient.id)
        
        assert stats["total_readings"] == 3
        assert stats["latest_reading_date"] is not None
        assert abs(stats["avg_systolic_bp"] - 120.0) < 0.1  # (120+125+115)/3 = 120
        assert abs(stats["avg_diastolic_bp"] - 80.0) < 0.1   # (80+85+75)/3 = 80
        assert abs(stats["avg_heart_rate"] - 72.3) < 0.1     # (72+75+70)/3 = 72.33
        assert stats["current_weight"] == 151.0  # Latest weight
        assert stats["current_bmi"] is not None
        assert abs(stats["weight_change"] - 1.0) < 0.1  # 151 - 150 = 1

    def test_get_vitals_stats_empty(self, db_session: Session, test_patient):
        """Test getting vitals statistics with no data."""
        stats = vitals_crud.get_vitals_stats(db_session, patient_id=test_patient.id)
        
        assert stats["total_readings"] == 0
        assert stats["latest_reading_date"] is None
        assert stats["avg_systolic_bp"] is None
        assert stats["avg_diastolic_bp"] is None
        assert stats["avg_heart_rate"] is None
        assert stats["current_weight"] is None
        assert stats["current_bmi"] is None

    def test_get_recent_readings(self, db_session: Session, test_patient):
        """Test getting recent vitals readings."""
        # Create vitals across different time periods
        dates = [
            datetime.now() - timedelta(days=45),  # Too old
            datetime.now() - timedelta(days=15),  # Recent
            datetime.now() - timedelta(days=5),   # Recent
            datetime.now() - timedelta(days=1)    # Recent
        ]
        
        for i, date in enumerate(dates):
            vitals_data = VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=date,
                systolic_bp=120 + i,
                diastolic_bp=80 + i,
                heart_rate=72 + i
            )
            vitals_crud.create(db_session, obj_in=vitals_data)
        
        # Get recent readings (last 30 days)
        recent_vitals = vitals_crud.get_recent_readings(
            db_session, patient_id=test_patient.id, days=30
        )
        
        assert len(recent_vitals) == 3  # Should exclude the 45-day old reading

    def test_update_vitals(self, db_session: Session, test_patient):
        """Test updating vitals."""
        # Create vitals
        vitals_data = VitalsCreate(
            patient_id=test_patient.id,
            recorded_date=datetime(2024, 1, 1, 10, 0, 0),
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            temperature=98.6
        )
        
        created_vitals = vitals_crud.create(db_session, obj_in=vitals_data)
        
        # Update vitals
        update_data = VitalsUpdate(
            systolic_bp=125,
            diastolic_bp=85,
            notes="Updated blood pressure readings"
        )
        
        updated_vitals = vitals_crud.update(
            db_session, db_obj=created_vitals, obj_in=update_data
        )
        
        assert updated_vitals.systolic_bp == 125
        assert updated_vitals.diastolic_bp == 85
        assert updated_vitals.notes == "Updated blood pressure readings"
        assert updated_vitals.heart_rate == 72  # Unchanged

    def test_delete_vitals(self, db_session: Session, test_patient):
        """Test deleting vitals."""
        # Create vitals
        vitals_data = VitalsCreate(
            patient_id=test_patient.id,
            recorded_date=datetime(2024, 1, 1, 10, 0, 0),
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72
        )
        
        created_vitals = vitals_crud.create(db_session, obj_in=vitals_data)
        vitals_id = created_vitals.id
        
        # Delete vitals
        deleted_vitals = vitals_crud.delete(db_session, id=vitals_id)
        
        assert deleted_vitals is not None
        assert deleted_vitals.id == vitals_id
        
        # Verify vitals is deleted
        retrieved_vitals = vitals_crud.get(db_session, id=vitals_id)
        assert retrieved_vitals is None

    def test_vitals_date_ordering(self, db_session: Session, test_patient):
        """Test that vitals are properly ordered by date."""
        # Create vitals with different dates
        dates = [
            datetime(2024, 1, 3, 10, 0, 0),
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 10, 0, 0)
        ]
        
        created_vitals = []
        for i, date in enumerate(dates):
            vitals_data = VitalsCreate(
                patient_id=test_patient.id,
                recorded_date=date,
                systolic_bp=120 + i,
                diastolic_bp=80 + i,
                heart_rate=72 + i
            )
            created_vitals.append(vitals_crud.create(db_session, obj_in=vitals_data))
        
        # Get vitals by blood pressure type (should be ordered by date desc)
        bp_readings = vitals_crud.get_by_vital_type(
            db_session, patient_id=test_patient.id, vital_type="blood_pressure"
        )
        
        assert len(bp_readings) == 3
        # Should be ordered by date descending (newest first)
        assert bp_readings[0].recorded_date > bp_readings[1].recorded_date
        assert bp_readings[1].recorded_date > bp_readings[2].recorded_date