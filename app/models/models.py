from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    column,
    func,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship as orm_relationship

# Import status enums for consistent status management
from .enums import (
    AllergyStatus,
    ConditionStatus,
    ConditionType,
    EncounterPriority,
    FamilyRelationship,
    InsuranceStatus,
    InsuranceType,
    LabResultStatus,
    MedicationStatus,
    ProcedureStatus,
    SeverityLevel,
    TreatmentStatus,
    get_all_allergy_statuses,
    get_all_condition_statuses,
    get_all_condition_types,
    get_all_encounter_priorities,
    get_all_family_relationships,
    get_all_insurance_statuses,
    get_all_insurance_types,
    get_all_lab_result_statuses,
    get_all_medication_statuses,
    get_all_procedure_statuses,
    get_all_severity_levels,
    get_all_treatment_statuses,
)


# Timezone-aware datetime function to replace deprecated datetime.utcnow()
def get_utc_now():
    """Get the current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)  # Role-based access control
    role = Column(
        String, nullable=False
    )  # e.g., 'admin', 'user', 'guest'    # Timestamps
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # V1: Current patient context - which patient they're managing
    active_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    # Original relationship (specify foreign key to avoid ambiguity)
    patient = orm_relationship(
        "Patient", foreign_keys="Patient.user_id", back_populates="user", uselist=False
    )

    # V1: New relationships
    owned_patients = orm_relationship(
        "Patient", foreign_keys="Patient.owner_user_id", overlaps="owner"
    )
    current_patient_context = orm_relationship(
        "Patient", foreign_keys=[active_patient_id]
    )

    # V1: Patient sharing relationships
    shared_patients_by_me = orm_relationship(
        "PatientShare",
        foreign_keys="PatientShare.shared_by_user_id",
        overlaps="shared_by",
    )
    shared_patients_with_me = orm_relationship(
        "PatientShare",
        foreign_keys="PatientShare.shared_with_user_id",
        overlaps="shared_with",
    )


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # V1: Individual ownership
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_self_record = Column(Boolean, default=False, nullable=False)

    # V2+: Family context (nullable for V1)
    family_id = Column(Integer, nullable=True)  # Will add FK constraint in V2
    relationship_to_family = Column(
        String, nullable=True
    )  # self, spouse, child, parent

    # V3+: Advanced permissions (nullable for V1/V2)
    privacy_level = Column(String, default="owner", nullable=False)

    # V4+: External linking (nullable for V1/V2/V3)
    external_account_id = Column(Integer, nullable=True)  # Will add FK constraint in V4
    is_externally_accessible = Column(Boolean, default=False, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)

    physician_id = Column(
        Integer, ForeignKey("practitioners.id"), nullable=True
    )  # Primary care physician

    blood_type = Column(String, nullable=True)  # e.g., 'A+', 'O-', etc.
    height = Column(Float, nullable=True)  # in inches
    weight = Column(Float, nullable=True)  # in lbs
    gender = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    owner = orm_relationship(
        "User", foreign_keys=[owner_user_id], overlaps="owned_patients"
    )
    user = orm_relationship("User", foreign_keys=[user_id], back_populates="patient")
    practitioner = orm_relationship("Practitioner", back_populates="patients")
    medications = orm_relationship(
        "Medication", back_populates="patient", cascade="all, delete-orphan"
    )
    encounters = orm_relationship(
        "Encounter", back_populates="patient", cascade="all, delete-orphan"
    )
    lab_results = orm_relationship(
        "LabResult", back_populates="patient", cascade="all, delete-orphan"
    )
    immunizations = orm_relationship(
        "Immunization", back_populates="patient", cascade="all, delete-orphan"
    )
    conditions = orm_relationship(
        "Condition", back_populates="patient", cascade="all, delete-orphan"
    )
    procedures = orm_relationship(
        "Procedure", back_populates="patient", cascade="all, delete-orphan"
    )
    treatments = orm_relationship(
        "Treatment", back_populates="patient", cascade="all, delete-orphan"
    )
    allergies = orm_relationship(
        "Allergy", back_populates="patient", cascade="all, delete-orphan"
    )
    vitals = orm_relationship(
        "Vitals", back_populates="patient", cascade="all, delete-orphan"
    )
    emergency_contacts = orm_relationship(
        "EmergencyContact", back_populates="patient", cascade="all, delete-orphan"
    )
    family_members = orm_relationship(
        "FamilyMember", back_populates="patient", cascade="all, delete-orphan"
    )
    insurances = orm_relationship(
        "Insurance", back_populates="patient", cascade="all, delete-orphan"
    )

    # V1: Patient sharing relationships
    shares = orm_relationship(
        "PatientShare",
        foreign_keys="PatientShare.patient_id",
        cascade="all, delete-orphan",
        overlaps="patient",
    )


class Practitioner(Base):
    __tablename__ = "practitioners"
    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    practice = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    website = Column(String, nullable=True)
    rating = Column(Float, nullable=True)  # Rating from 0.0 to 5.0

    # Table Relationships
    patients = orm_relationship("Patient", back_populates="practitioner")
    medications = orm_relationship("Medication", back_populates="practitioner")
    encounters = orm_relationship("Encounter", back_populates="practitioner")
    lab_results = orm_relationship("LabResult", back_populates="practitioner")
    immunizations = orm_relationship("Immunization", back_populates="practitioner")
    procedures = orm_relationship("Procedure", back_populates="practitioner")
    treatments = orm_relationship("Treatment", back_populates="practitioner")
    conditions = orm_relationship("Condition", back_populates="practitioner")
    vitals = orm_relationship("Vitals", back_populates="practitioner")


class Medication(Base):
    """
    Represents a medication
    """

    __tablename__ = "medications"
    id = Column(Integer, primary_key=True)

    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    route = Column(
        String, nullable=True
    )  # How it is administered (e.g., oral, injection, etc.)
    indication = Column(String, nullable=True)  # What the medication is prescribed for
    effective_period_start = Column(Date, nullable=True)  # Start date of the medication
    effective_period_end = Column(Date, nullable=True)  # End date of the medication
    status = Column(
        String, nullable=True
    )  # Use MedicationStatus enum: active, inactive, on_hold, completed, cancelled
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="medications")
    practitioner = orm_relationship("Practitioner", back_populates="medications")
    pharmacy = orm_relationship("Pharmacy", back_populates="medications")
    allergies = orm_relationship("Allergy", back_populates="medication")

    # Many-to-Many relationship with conditions through junction table
    condition_relationships = orm_relationship(
        "ConditionMedication", back_populates="medication", cascade="all, delete-orphan"
    )


class Encounter(Base):
    """
    Represents a medical encounter between a patient and a practitioner.
    """

    __tablename__ = "encounters"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"))
    condition_id = Column(Integer, ForeignKey("conditions.id"), nullable=True)

    # Basic encounter information
    reason = Column(String, nullable=False)  # Reason for the encounter
    date = Column(Date, nullable=False)  # Date of the encounter
    notes = Column(String, nullable=True)  # Additional notes from the encounter

    # Enhanced encounter details (all optional)
    visit_type = Column(
        String, nullable=True
    )  # e.g., 'annual checkup', 'follow-up', 'consultation', 'emergency'
    chief_complaint = Column(
        String, nullable=True
    )  # Primary concern or symptom reported by patient
    diagnosis = Column(
        String, nullable=True
    )  # Clinical assessment or diagnosis from the visit
    treatment_plan = Column(
        String, nullable=True
    )  # Recommended treatment or next steps
    follow_up_instructions = Column(
        String, nullable=True
    )  # Follow-up care instructions
    duration_minutes = Column(
        Integer, nullable=True
    )  # Duration of the visit in minutes
    location = Column(
        String, nullable=True
    )  # Where visit occurred (office, hospital, telehealth, etc.)
    priority = Column(
        String, nullable=True
    )  # Use EncounterPriority enum: routine, urgent, emergency

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="encounters")
    practitioner = orm_relationship("Practitioner", back_populates="encounters")
    condition = orm_relationship("Condition")


class LabResult(Base):
    __tablename__ = "lab_results"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(
        Integer, ForeignKey("practitioners.id"), nullable=True
    )  # Ordering practitioner

    # Basic test information
    test_name = Column(String, nullable=False)  # Name/description of the test
    test_code = Column(String, nullable=True)  # Optional code (LOINC, CPT, etc.)
    test_category = Column(
        String, nullable=True
    )  # e.g., 'blood work', 'imaging', 'pathology'
    test_type = Column(String, nullable=True)  # e.g., 'routine', 'emergency', etc.
    facility = Column(String, nullable=True)  # Facility where the test was ordered
    status = Column(
        String, nullable=False, default="ordered"
    )  # Use LabResultStatus enum: ordered, in_progress, completed, cancelled
    labs_result = Column(
        String, nullable=True
    )  # Lab result interpretation: 'normal', 'abnormal', etc.
    ordered_date = Column(Date, nullable=True)  # When the test was ordered
    completed_date = Column(Date, nullable=True)  # When results were received

    # Optional notes
    notes = Column(Text, nullable=True)  # Any additional notes about the test

    # Audit fields
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="lab_results")
    practitioner = orm_relationship("Practitioner", back_populates="lab_results")

    # One-to-Many relationship with LabResultFile (actual test results: PDFs, images, etc.)
    files = orm_relationship(
        "LabResultFile", back_populates="lab_result", cascade="all, delete-orphan"
    )

    # Many-to-Many relationship with conditions through junction table
    condition_relationships = orm_relationship(
        "LabResultCondition", back_populates="lab_result", cascade="all, delete-orphan"
    )


class LabResultFile(Base):
    __tablename__ = "lab_result_files"
    id = Column(Integer, primary_key=True)

    lab_result_id = Column(Integer, ForeignKey("lab_results.id"))
    file_name = Column(String, nullable=False)  # Name of the file
    file_path = Column(String, nullable=False)  # Path to the file on the server
    file_type = Column(String, nullable=False)  # e.g., 'pdf', 'image/png', etc.
    file_size = Column(Integer, nullable=True)  # Size of the file in bytes
    description = Column(String, nullable=True)  # Optional description of the file
    uploaded_at = Column(
        DateTime, nullable=False
    )  # Timestamp of when the file was uploaded

    # Table Relationships
    lab_result = orm_relationship("LabResult", back_populates="files")


class EntityFile(Base):
    """
    Generic file management for all entity types.
    Supports lab-results, insurance, visits, procedures, and future entity types.
    """

    __tablename__ = "entity_files"

    id = Column(Integer, primary_key=True)
    entity_type = Column(
        String(50), nullable=False
    )  # 'lab-result', 'insurance', 'visit', 'procedure'
    entity_id = Column(Integer, nullable=False)  # Foreign key to the entity
    file_name = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Path to file on server
    file_type = Column(String(100), nullable=False)  # MIME type or extension
    file_size = Column(Integer, nullable=True)  # Size in bytes
    description = Column(Text, nullable=True)  # Optional description
    category = Column(
        String(100), nullable=True
    )  # File category (result, report, card, etc.)
    uploaded_at = Column(DateTime, nullable=False)  # Upload timestamp

    # Storage backend tracking
    storage_backend = Column(
        String(20), default="local", nullable=False
    )  # 'local' or 'paperless'
    paperless_document_id = Column(
        String(255), nullable=True
    )  # ID in paperless-ngx system
    sync_status = Column(
        String(20), default="synced", nullable=False
    )  # 'synced', 'pending', 'processing', 'failed', 'missing'
    last_sync_at = Column(DateTime, nullable=True)  # Last successful sync timestamp

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    updated_at = Column(
        DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_entity_type_id", "entity_type", "entity_id"),
        Index("idx_category", "category"),
        Index("idx_uploaded_at", "uploaded_at"),
        Index("idx_created_at", "created_at"),
        Index("idx_storage_backend", "storage_backend"),
        Index("idx_paperless_document_id", "paperless_document_id"),
        Index("idx_sync_status", "sync_status"),
    )


class LabResultCondition(Base):
    """
    Junction table for many-to-many relationship between lab results and conditions.
    Allows one lab result to be related to multiple conditions with optional context.
    """

    __tablename__ = "lab_result_conditions"

    id = Column(Integer, primary_key=True)
    lab_result_id = Column(Integer, ForeignKey("lab_results.id"), nullable=False)
    condition_id = Column(Integer, ForeignKey("conditions.id"), nullable=False)

    # Optional context about how this lab result relates to this condition
    relevance_note = Column(
        String, nullable=True
    )  # e.g., "Elevated glucose indicates poor control"

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    lab_result = orm_relationship("LabResult", back_populates="condition_relationships")
    condition = orm_relationship("Condition", back_populates="lab_result_relationships")


class ConditionMedication(Base):
    """
    Junction table for many-to-many relationship between conditions and medications.
    Allows one condition to be related to multiple medications with optional context.
    """

    __tablename__ = "condition_medications"

    id = Column(Integer, primary_key=True)
    condition_id = Column(Integer, ForeignKey("conditions.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)

    # Optional context about how this medication relates to this condition
    relevance_note = Column(
        String, nullable=True
    )  # e.g., "Primary treatment for hypertension"

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    condition = orm_relationship("Condition", back_populates="medication_relationships")
    medication = orm_relationship(
        "Medication", back_populates="condition_relationships"
    )


class Condition(Base):
    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)

    # Condition details
    condition_name = Column(String, nullable=True)  # Name of the condition
    diagnosis = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    onset_date = Column(
        Date, nullable=True
    )  # Date when the condition was first diagnosed
    status = Column(
        String, nullable=False
    )  # Use ConditionStatus enum: active, inactive, resolved, chronic, recurrence, relapse
    end_date = Column(Date, nullable=True)  # Date when the condition was resolved

    # Severity and medical codes
    severity = Column(
        String, nullable=True
    )  # Use SeverityLevel enum: mild, moderate, severe, critical
    icd10_code = Column(String, nullable=True)  # ICD-10 diagnosis code
    snomed_code = Column(String, nullable=True)  # SNOMED CT code
    code_description = Column(String, nullable=True)  # Description of the medical code

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="conditions")
    practitioner = orm_relationship("Practitioner", back_populates="conditions")
    treatments = orm_relationship("Treatment", back_populates="condition")
    # encounters relationship removed - use queries instead due to potential high volume
    procedures = orm_relationship("Procedure", back_populates="condition")

    # Many-to-Many relationship with lab results through junction table
    lab_result_relationships = orm_relationship(
        "LabResultCondition", back_populates="condition", cascade="all, delete-orphan"
    )

    # Many-to-Many relationship with medications through junction table
    medication_relationships = orm_relationship(
        "ConditionMedication", back_populates="condition", cascade="all, delete-orphan"
    )


class Immunization(Base):
    __tablename__ = "immunizations"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)

    # Primary vaccine information
    vaccine_name = Column(String, nullable=False)  # Name of the vaccine
    date_administered = Column(Date, nullable=False)  # Date when administered
    dose_number = Column(Integer, nullable=True)  # Dose number in series

    # Vaccine details
    lot_number = Column(String, nullable=True)  # Vaccine lot number
    manufacturer = Column(String, nullable=True)  # Vaccine manufacturer
    site = Column(String, nullable=True)  # Injection site
    route = Column(String, nullable=True)  # Route of administration
    expiration_date = Column(Date, nullable=True)  # Vaccine expiration date
    notes = Column(Text, nullable=True)  # Additional notes

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="immunizations")
    practitioner = orm_relationship("Practitioner", back_populates="immunizations")


class Procedure(Base):
    __tablename__ = "procedures"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)
    condition_id = Column(Integer, ForeignKey("conditions.id"), nullable=True)

    procedure_name = Column(String, nullable=False)  # Name of the procedure
    procedure_type = Column(
        String, nullable=True
    )  # Type of procedure (e.g., surgical, diagnostic, etc.)
    procedure_code = Column(
        String, nullable=True
    )  # Code for the procedure (e.g., CPT code)
    date = Column(Date, nullable=False)  # Date when the procedure was performed
    description = Column(String, nullable=True)  # Description of the procedure
    status = Column(
        String, nullable=True
    )  # Use ProcedureStatus enum: scheduled, in_progress, completed, cancelled
    notes = Column(String, nullable=True)  # Additional notes about the procedure
    facility = Column(
        String, nullable=True
    )  # Facility where the procedure was performed
    procedure_setting = Column(
        String, nullable=True
    )  # Setting of procedure (e.g., outpatient, inpatient, office, etc)
    procedure_complications = Column(
        String, nullable=True
    )  # Any complications that occured during the procedure
    procedure_duration = Column(
        Integer, nullable=True
    )  # Duration of the procedure in minutes

    anesthesia_type = Column(
        String, nullable=True
    )  # Type of anesthesia used (e.g., local, regional, general)
    anesthesia_notes = Column(
        String, nullable=True
    )  # Additional notes about the anesthesia

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="procedures")
    practitioner = orm_relationship("Practitioner", back_populates="procedures")
    condition = orm_relationship("Condition", back_populates="procedures")


class Treatment(Base):
    __tablename__ = "treatments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)
    condition_id = Column(Integer, ForeignKey("conditions.id"), nullable=True)

    treatment_name = Column(String, nullable=False)  # Name of the treatment
    treatment_type = Column(
        String, nullable=False
    )  # Type of treatment (e.g., 'physical therapy', 'surgery')
    start_date = Column(Date, nullable=False)  # Start date of the treatment
    end_date = Column(Date, nullable=True)  # End date of the treatment (if applicable)
    status = Column(
        String, nullable=True
    )  # Use TreatmentStatus enum: active, in_progress, completed, cancelled, on_hold
    treatment_category = Column(
        String, nullable=True
    )  # Category of treatment (e.g., 'inpatient', 'outpatient')
    notes = Column(String, nullable=True)  # Additional notes about the treatment
    frequency = Column(
        String, nullable=True
    )  # Frequency of the treatment (e.g., 'daily', 'weekly')
    outcome = Column(String, nullable=True)  # Expected outcome of the treatment
    description = Column(String, nullable=True)  # Description of the treatment
    location = Column(
        String, nullable=True
    )  # Location where the treatment is administered
    dosage = Column(String, nullable=True)  # Dosage of the treatment

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="treatments")
    practitioner = orm_relationship("Practitioner", back_populates="treatments")
    condition = orm_relationship("Condition", back_populates="treatments")


class Allergy(Base):
    __tablename__ = "allergies"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)

    allergen = Column(String, nullable=False)  # Allergen name
    reaction = Column(String, nullable=False)  # Reaction to the allergen
    severity = Column(
        String, nullable=True
    )  # Use SeverityLevel enum: mild, moderate, severe, critical
    onset_date = Column(Date, nullable=True)  # Date when the allergy was first noted
    status = Column(
        String, nullable=True
    )  # Use AllergyStatus enum: active, inactive, resolved
    notes = Column(String, nullable=True)  # Additional notes about the allergy

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="allergies")
    medication = orm_relationship("Medication", back_populates="allergies")


class Vitals(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"), nullable=True)

    # Date and time when vitals were recorded
    recorded_date = Column(DateTime, nullable=False)

    # Vital sign measurements
    systolic_bp = Column(Integer, nullable=True)  # Systolic blood pressure (mmHg)
    diastolic_bp = Column(Integer, nullable=True)  # Diastolic blood pressure (mmHg)
    heart_rate = Column(Integer, nullable=True)  # Heart rate (bpm)
    temperature = Column(Float, nullable=True)  # Body temperature (Fahrenheit)
    weight = Column(Float, nullable=True)  # Weight (lbs)
    height = Column(Float, nullable=True)  # Height (inches)
    oxygen_saturation = Column(Float, nullable=True)  # SpO2 percentage
    respiratory_rate = Column(Integer, nullable=True)  # Breaths per minute
    blood_glucose = Column(Float, nullable=True)  # Blood glucose (mg/dL)

    # Additional measurements
    bmi = Column(Float, nullable=True)  # Body Mass Index (calculated)
    pain_scale = Column(Integer, nullable=True)  # Pain scale 0-10

    # Optional notes and metadata
    notes = Column(Text, nullable=True)  # Additional notes about the readings
    location = Column(
        String, nullable=True
    )  # Where readings were taken (home, clinic, etc.)
    device_used = Column(
        String, nullable=True
    )  # Device used for measurement    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="vitals")
    practitioner = orm_relationship("Practitioner", back_populates="vitals")


class Pharmacy(Base):
    __tablename__ = "pharmacies"
    id = Column(Integer, primary_key=True)

    # Descriptive name that includes location context
    name = Column(
        String, nullable=False
    )  # e.g., "CVS Pharmacy - Main Street", "Walgreens - Downtown"
    brand = Column(String, nullable=True)  # e.g., 'CVS', 'Walgreens', 'Independent'

    # Detailed address components for better identification
    street_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True)  # e.g., 'USA', 'Canada'

    # Optional store identifier from the pharmacy chain
    store_number = Column(String, nullable=True)  # CVS store #1234, Walgreens #5678

    # Contact information
    phone_number = Column(String, nullable=True)
    fax_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Operating hours (could be JSON or separate table if more complex)
    hours = Column(String, nullable=True)  # e.g., "Mon-Fri: 8AM-10PM, Sat-Sun: 9AM-9PM"

    # Pharmacy-specific features
    drive_through = Column(
        Boolean, nullable=True, default=False
    )  # Boolean for drive-through availability
    twenty_four_hour = Column(
        Boolean, nullable=True, default=False
    )  # Boolean for 24-hour service
    specialty_services = Column(
        String, nullable=True
    )  # e.g., "Vaccinations, Medication Therapy Management"

    # Timestamps
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    medications = orm_relationship("Medication", back_populates="pharmacy")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Contact Information
    name = Column(String, nullable=False)  # Full name of emergency contact
    relationship = Column(
        String, nullable=False
    )  # e.g., 'spouse', 'parent', 'child', 'friend', 'sibling'
    phone_number = Column(String, nullable=False)  # Primary phone number
    secondary_phone = Column(String, nullable=True)  # Optional secondary phone
    email = Column(String, nullable=True)  # Optional email address

    # Priority and Status
    is_primary = Column(
        Boolean, default=False, nullable=False
    )  # Primary emergency contact
    is_active = Column(Boolean, default=True, nullable=False)  # Active/inactive status

    # Additional Details
    address = Column(String, nullable=True)  # Contact's address
    notes = Column(
        String, nullable=True
    )  # Additional notes (e.g., "Available weekdays only")

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="emergency_contacts")


class BackupRecord(Base):
    """
    Represents a backup record for tracking backup operations.
    """

    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True)
    backup_type = Column(String, nullable=False)  # 'full', 'database', 'files'
    status = Column(String, nullable=False)  # 'created', 'failed', 'verified'
    file_path = Column(String, nullable=False)  # Path to the backup file
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    size_bytes = Column(Integer, nullable=True)  # Size of backup file in bytes
    description = Column(Text, nullable=True)  # Optional description

    # Optional metadata
    compression_used = Column(Boolean, default=False, nullable=False)
    checksum = Column(String, nullable=True)  # File checksum for integrity verification


class FamilyMember(Base):
    """
    Represents a family member for tracking family medical history.
    """

    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Basic Information
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)  # Use FamilyRelationship enum
    gender = Column(String, nullable=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    is_deceased = Column(Boolean, default=False, nullable=False)

    # Additional information
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    patient = orm_relationship("Patient", back_populates="family_members")
    family_conditions = orm_relationship(
        "FamilyCondition", back_populates="family_member", cascade="all, delete-orphan"
    )
    shares = orm_relationship(
        "FamilyHistoryShare",
        back_populates="family_member",
        cascade="all, delete-orphan",
    )


class FamilyCondition(Base):
    """
    Represents a medical condition for a family member.
    """

    __tablename__ = "family_conditions"

    id = Column(Integer, primary_key=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)

    # Condition Information
    condition_name = Column(String, nullable=False)
    diagnosis_age = Column(Integer, nullable=True)  # Age when diagnosed
    severity = Column(String, nullable=True)  # Use SeverityLevel enum
    status = Column(String, nullable=True)  # active, resolved, chronic
    condition_type = Column(String, nullable=True)  # Use ConditionType enum
    notes = Column(Text, nullable=True)

    # Medical Codes (optional)
    icd10_code = Column(String, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    family_member = orm_relationship("FamilyMember", back_populates="family_conditions")


class PatientShare(Base):
    """_summary_

    Args:
        Base (_type_): _description_
    """

    __tablename__ = "patient_shares"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Permission control
    permission_level = Column(String, nullable=False)  # view, edit, full
    custom_permissions = Column(JSON, nullable=True)

    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    patient = orm_relationship("Patient", foreign_keys=[patient_id], overlaps="shares")
    shared_by = orm_relationship(
        "User", foreign_keys=[shared_by_user_id], overlaps="shared_patients_by_me"
    )
    shared_with = orm_relationship(
        "User", foreign_keys=[shared_with_user_id], overlaps="shared_patients_with_me"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "patient_id", "shared_with_user_id", name="unique_patient_share"
        ),
    )


class Invitation(Base):
    """Reusable invitation system for various sharing/collaboration features"""

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)

    # Who's sending and receiving
    sent_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What type of invitation
    invitation_type = Column(
        String, nullable=False
    )  # 'family_history_share', 'patient_share', 'family_join', etc.

    # Status tracking
    status = Column(
        String, default="pending", nullable=False
    )  # pending, accepted, rejected, expired, cancelled

    # Invitation details
    title = Column(String, nullable=False)  # "Family History Share Request"
    message = Column(Text, nullable=True)  # Custom message from sender

    # Context data (JSON for flexibility)
    context_data = Column(JSON, nullable=False)  # Stores type-specific data

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Response tracking
    responded_at = Column(DateTime, nullable=True)
    response_note = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    sent_by = orm_relationship("User", foreign_keys=[sent_by_user_id])
    sent_to = orm_relationship("User", foreign_keys=[sent_to_user_id])

    # No unique constraints - let application logic handle business rules
    # Each invitation has a unique ID which is sufficient for database integrity


class FamilyHistoryShare(Base):
    """Share family history records independently from personal medical data"""

    __tablename__ = "family_history_shares"

    id = Column(Integer, primary_key=True)

    # Link to the invitation that created this share
    invitation_id = Column(Integer, ForeignKey("invitations.id"), nullable=False)

    # What's being shared - specific family member's history record
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)

    # Who's sharing and receiving
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Simple permissions
    permission_level = Column(
        String, default="view", nullable=False
    )  # view only for Phase 1.5
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Optional sharing note
    sharing_note = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    invitation = orm_relationship("Invitation")
    family_member = orm_relationship("FamilyMember", back_populates="shares")
    shared_by = orm_relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = orm_relationship("User", foreign_keys=[shared_with_user_id])

    # Constraints - allow multiple shares but only one active share per family member/user pair
    __table_args__ = (
        # Partial unique constraint: only one active share per (family_member_id, shared_with_user_id)
        # Multiple inactive shares are allowed to maintain history
        Index(
            "unique_active_family_history_share_partial",
            "family_member_id",
            "shared_with_user_id",
            unique=True,
            postgresql_where=(column("is_active") == True),
        ),
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Unit system preference: 'imperial' or 'metric'
    unit_system = Column(String, default="imperial", nullable=False)

    # Paperless-ngx integration fields
    paperless_enabled = Column(Boolean, default=False, nullable=False)
    paperless_url = Column(String(500), nullable=True)
    paperless_api_token_encrypted = Column(Text, nullable=True)  # Encrypted API token
    paperless_username_encrypted = Column(Text, nullable=True)  # Encrypted username
    paperless_password_encrypted = Column(Text, nullable=True)  # Encrypted password
    default_storage_backend = Column(
        String(20), default="local", nullable=False
    )  # 'local' or 'paperless'
    paperless_auto_sync = Column(Boolean, default=False, nullable=False)
    paperless_sync_tags = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Relationships
    user = orm_relationship("User", backref="preferences")


class Insurance(Base):
    """
    Represents insurance information for a patient.
    Supports multiple insurance types: medical, dental, vision, prescription.
    """

    __tablename__ = "insurances"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Insurance type and basic info
    insurance_type = Column(
        String, nullable=False
    )  # Use InsuranceType enum: medical, dental, vision, prescription
    company_name = Column(String, nullable=False)
    employer_group = Column(
        String, nullable=True
    )  # Company or organization providing the insurance
    member_name = Column(String, nullable=False)
    member_id = Column(String, nullable=False)
    group_number = Column(String, nullable=True)
    plan_name = Column(String, nullable=True)

    # Policy holder information (may differ from member)
    policy_holder_name = Column(String, nullable=True)
    relationship_to_holder = Column(
        String, nullable=True
    )  # self, spouse, child, dependent

    # Coverage period
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)

    # Status management
    status = Column(
        String, nullable=False, default="active"
    )  # Use InsuranceStatus enum: active, inactive, expired, pending
    is_primary = Column(
        Boolean, default=False, nullable=False
    )  # For medical insurance hierarchy

    # Type-specific data stored as JSON for flexibility
    coverage_details = Column(
        JSON, nullable=True
    )  # Copays, deductibles, percentages, BIN/PCN, etc.
    contact_info = Column(JSON, nullable=True)  # Phone numbers, addresses, websites

    # General notes
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False
    )

    # Table Relationships
    patient = orm_relationship("Patient", back_populates="insurances")
