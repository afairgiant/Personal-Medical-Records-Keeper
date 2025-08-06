"""
Test data utilities for creating mock medical records.
"""
import random
from datetime import date, datetime, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.crud import medication, lab_result, practitioner, vitals
from app.models.models import Patient


def create_sample_medication(db: Session, patient: Patient) -> dict:
    """Create a sample medication record."""
    medication_names = [
        "Lisinopril", "Metformin", "Amlodipine", "Omeprazole", 
        "Simvastatin", "Aspirin", "Ibuprofen", "Acetaminophen"
    ]
    
    frequencies = ["Daily", "Twice daily", "Three times daily", "Weekly", "As needed"]
    dosages = ["5mg", "10mg", "20mg", "25mg", "50mg", "100mg", "500mg"]
    
    data = {
        "patient_id": patient.id,
        "name": random.choice(medication_names),
        "dosage": random.choice(dosages),
        "frequency": random.choice(frequencies),
        "start_date": date.today() - timedelta(days=random.randint(1, 365)),
        "end_date": None if random.random() > 0.3 else date.today() + timedelta(days=random.randint(1, 180)),
        "prescribing_doctor": f"Dr. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}",
        "notes": f"Prescribed for test condition {random.randint(1, 100)}",
        "status": random.choice(["active", "inactive", "discontinued"])
    }
    
    return medication.create(db=db, obj_in=data)


def create_sample_lab_result(db: Session, patient: Patient) -> dict:
    """Create a sample lab result record."""
    test_names = [
        "Complete Blood Count", "Basic Metabolic Panel", "Lipid Panel",
        "Liver Function Tests", "Thyroid Function", "Hemoglobin A1C",
        "Urinalysis", "Vitamin D", "PSA", "Mammogram"
    ]
    
    results = ["Normal", "Abnormal", "High", "Low", "Borderline"]
    labs = ["LabCorp", "Quest", "Hospital Lab", "Clinic Lab"]
    
    data = {
        "patient_id": patient.id,
        "test_name": random.choice(test_names),
        "test_date": date.today() - timedelta(days=random.randint(1, 365)),
        "result": random.choice(results),
        "reference_range": "Within normal limits",
        "ordering_doctor": f"Dr. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}",
        "lab_name": random.choice(labs),
        "notes": f"Test result notes {random.randint(1, 100)}",
        "status": "completed"
    }
    
    return lab_result.create(db=db, obj_in=data)


def create_sample_practitioner(db: Session) -> dict:
    """Create a sample practitioner record."""
    names = ["Dr. John Smith", "Dr. Jane Wilson", "Dr. Michael Brown", "Dr. Sarah Davis"]
    specialties = [
        "Family Medicine", "Internal Medicine", "Cardiology", "Dermatology",
        "Endocrinology", "Gastroenterology", "Neurology", "Orthopedics"
    ]
    
    data = {
        "name": random.choice(names),
        "specialty": random.choice(specialties),
        "phone_number": f"555-{random.randint(1000, 9999)}",
        "email": f"doctor{random.randint(1, 1000)}@example.com",
        "address": f"{random.randint(100, 9999)} Medical Center Dr",
        "website": f"https://doctor{random.randint(1, 1000)}.com",
        "rating": round(random.uniform(3.0, 5.0), 1),
        "status": "active"
    }
    
    return practitioner.create(db=db, obj_in=data)


def create_sample_vitals(db: Session, patient: Patient) -> dict:
    """Create a sample vitals record."""
    data = {
        "patient_id": patient.id,
        "measurement_date": date.today() - timedelta(days=random.randint(1, 30)),
        "systolic_bp": random.randint(110, 140),
        "diastolic_bp": random.randint(70, 90),
        "heart_rate": random.randint(60, 100),
        "temperature": round(random.uniform(97.0, 99.5), 1),
        "weight": random.randint(120, 250),
        "height": random.randint(60, 76),
        "bmi": round(random.uniform(18.5, 35.0), 1),
        "notes": f"Vital signs recorded {random.randint(1, 100)}"
    }
    
    return vitals.create(db=db, obj_in=data)


def create_bulk_test_data(db: Session, patient: Patient, count: int = 5) -> Dict[str, list]:
    """Create bulk test data for a patient."""
    medications = [create_sample_medication(db, patient) for _ in range(count)]
    lab_results = [create_sample_lab_result(db, patient) for _ in range(count)]
    vital_records = [create_sample_vitals(db, patient) for _ in range(count)]
    
    # Create some practitioners (not patient-specific)
    practitioners = [create_sample_practitioner(db) for _ in range(3)]
    
    return {
        "medications": medications,
        "lab_results": lab_results,
        "vitals": vital_records,
        "practitioners": practitioners
    }


def create_test_condition_data() -> Dict[str, Any]:
    """Create test data for medical conditions."""
    conditions = [
        "Hypertension", "Diabetes Type 2", "Hyperlipidemia", "Asthma",
        "Depression", "Anxiety", "Arthritis", "GERD"
    ]
    
    severities = ["mild", "moderate", "severe"]
    statuses = ["active", "resolved", "chronic"]
    
    return {
        "name": random.choice(conditions),
        "description": f"Test condition description {random.randint(1, 100)}",
        "diagnosis_date": date.today() - timedelta(days=random.randint(1, 1000)),
        "status": random.choice(statuses),
        "severity": random.choice(severities),
        "notes": f"Condition notes {random.randint(1, 100)}"
    }


def create_test_allergy_data() -> Dict[str, Any]:
    """Create test data for allergies."""
    allergens = [
        "Penicillin", "Sulfa", "Shellfish", "Nuts", "Eggs", 
        "Milk", "Latex", "Pollen", "Dust"
    ]
    
    reactions = [
        "Rash", "Hives", "Swelling", "Difficulty breathing",
        "Nausea", "Vomiting", "Anaphylaxis"
    ]
    
    severities = ["mild", "moderate", "severe"]
    
    return {
        "allergen": random.choice(allergens),
        "reaction": random.choice(reactions),
        "severity": random.choice(severities),
        "onset_date": date.today() - timedelta(days=random.randint(1, 1000)),
        "notes": f"Allergy notes {random.randint(1, 100)}",
        "status": "active"
    }


def create_test_immunization_data() -> Dict[str, Any]:
    """Create test data for immunizations."""
    vaccines = [
        "COVID-19 mRNA", "Influenza", "Tdap", "MMR", "Hepatitis B",
        "Pneumococcal", "Shingles", "HPV", "Meningitis"
    ]
    
    return {
        "vaccine_name": random.choice(vaccines),
        "vaccination_date": date.today() - timedelta(days=random.randint(1, 365)),
        "dose_number": random.randint(1, 3),
        "lot_number": f"LOT{random.randint(1000, 9999)}",
        "administered_by": f"Dr. {random.choice(['Smith', 'Johnson', 'Williams'])}",
        "location": random.choice(["Clinic", "Pharmacy", "Hospital"]),
        "notes": f"Vaccination notes {random.randint(1, 100)}",
        "status": "completed"
    }


def create_test_emergency_contact_data() -> Dict[str, Any]:
    """Create test data for emergency contacts."""
    relationships = ["Spouse", "Parent", "Child", "Sibling", "Friend", "Other"]
    
    return {
        "name": f"Emergency Contact {random.randint(1, 100)}",
        "relationship": random.choice(relationships),
        "phone_number": f"555-{random.randint(1000, 9999)}",
        "email": f"emergency{random.randint(1, 1000)}@example.com",
        "address": f"{random.randint(100, 9999)} Emergency St",
        "is_primary": random.choice([True, False]),
        "notes": f"Emergency contact notes {random.randint(1, 100)}"
    }


def create_performance_test_data(db: Session, patient: Patient, record_count: int = 100):
    """Create large dataset for performance testing."""
    print(f"Creating {record_count} records for performance testing...")
    
    # Create medications
    for i in range(record_count):
        create_sample_medication(db, patient)
        if i % 10 == 0:
            db.commit()  # Commit in batches
    
    # Create lab results  
    for i in range(record_count):
        create_sample_lab_result(db, patient)
        if i % 10 == 0:
            db.commit()
    
    # Create vitals
    for i in range(record_count):
        create_sample_vitals(db, patient)
        if i % 10 == 0:
            db.commit()
    
    db.commit()
    print(f"Created {record_count * 3} total records")


def clean_test_data(db: Session, patient_id: int):
    """Clean up test data for a specific patient."""
    # This would clean up all test records for the patient
    # Implementation depends on your CRUD operations
    pass