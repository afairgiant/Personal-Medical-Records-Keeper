from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, validator, field_validator

# Import status enums for validation
from ..models.enums import get_all_condition_statuses, get_all_severity_levels


class ConditionBase(BaseModel):
    diagnosis: str = Field(
        ..., min_length=2, max_length=500, description="Medical diagnosis"
    )
    condition_name: Optional[str] = Field(
        None, max_length=200, description="Optional alternative name for the condition"
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes about the condition"
    )
    onset_date: Optional[date] = Field(
        None, description="Date when the condition was first diagnosed"
    )
    end_date: Optional[date] = Field(
        None, description="Date when the condition was resolved"
    )
    status: str = Field(..., description="Status of the condition")
    severity: Optional[str] = Field(None, description="Severity of the condition")
    icd10_code: Optional[str] = Field(
        None, max_length=10, description="ICD-10 diagnosis code"
    )
    snomed_code: Optional[str] = Field(
        None, max_length=20, description="SNOMED CT code"
    )
    code_description: Optional[str] = Field(
        None, max_length=500, description="Description of the medical code"
    )
    patient_id: int = Field(..., gt=0, description="ID of the patient")
    practitioner_id: Optional[int] = Field(
        None, gt=0, description="ID of the practitioner"
    )
    medication_id: Optional[int] = Field(
        None, gt=0, description="ID of related medication"
    )

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = get_all_condition_statuses()
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()

    @validator("onset_date")
    def validate_onset_date(cls, v):
        if v and v > date.today():
            raise ValueError("Onset date cannot be in the future")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v:
            if v > date.today():
                raise ValueError("End date cannot be in the future")
            if (
                "onset_date" in values
                and values["onset_date"]
                and v < values["onset_date"]
            ):
                raise ValueError("End date cannot be before onset date")
        return v

    @validator("severity")
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = get_all_severity_levels()
            if v.lower() not in valid_severities:
                raise ValueError(
                    f"Severity must be one of: {', '.join(valid_severities)}"
                )
            return v.lower()
        return v


class ConditionCreate(ConditionBase):
    pass


class ConditionUpdate(BaseModel):
    diagnosis: Optional[str] = Field(None, min_length=2, max_length=500)
    condition_name: Optional[str] = Field(
        None, max_length=200, description="Optional alternative name for the condition"
    )
    notes: Optional[str] = Field(None, max_length=1000)
    onset_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    icd10_code: Optional[str] = Field(None, max_length=10)
    snomed_code: Optional[str] = Field(None, max_length=20)
    code_description: Optional[str] = Field(None, max_length=500)
    practitioner_id: Optional[int] = Field(None, gt=0)
    medication_id: Optional[int] = Field(None, gt=0)

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = get_all_condition_statuses()
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v

    @validator("onset_date")
    def validate_onset_date(cls, v):
        if v and v > date.today():
            raise ValueError("Onset date cannot be in the future")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v:
            if v > date.today():
                raise ValueError("End date cannot be in the future")
            if (
                "onset_date" in values
                and values["onset_date"]
                and v < values["onset_date"]
            ):
                raise ValueError("End date cannot be before onset date")
        return v

    @validator("severity")
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = get_all_severity_levels()
            if v.lower() not in valid_severities:
                raise ValueError(
                    f"Severity must be one of: {', '.join(valid_severities)}"
                )
            return v.lower()
        return v


class ConditionResponse(ConditionBase):
    id: int

    class Config:
        from_attributes = True


class ConditionWithRelations(ConditionResponse):
    patient: Optional[dict] = None
    practitioner: Optional[dict] = None
    treatments: Optional[list] = None

    class Config:
        from_attributes = True
        
    @field_validator('patient', mode='before')
    @classmethod
    def validate_patient(cls, v):
        """Convert SQLAlchemy Patient object to dict"""
        if v is None:
            return None
        if hasattr(v, '__dict__'):
            # Convert SQLAlchemy object to dict
            return {
                'id': getattr(v, 'id', None),
                'first_name': getattr(v, 'first_name', None),
                'last_name': getattr(v, 'last_name', None),
                'birth_date': getattr(v, 'birth_date', None),
                'user_id': getattr(v, 'user_id', None),
            }
        return v
    
    @field_validator('practitioner', mode='before')
    @classmethod
    def validate_practitioner(cls, v):
        """Convert SQLAlchemy Practitioner object to dict"""
        if v is None:
            return None
        if hasattr(v, '__dict__'):
            # Convert SQLAlchemy object to dict
            return {
                'id': getattr(v, 'id', None),
                'name': getattr(v, 'name', None),
                'specialty': getattr(v, 'specialty', None),
                'phone_number': getattr(v, 'phone_number', None),
            }
        return v
    
    @field_validator('treatments', mode='before')
    @classmethod
    def validate_treatments(cls, v):
        """Convert SQLAlchemy Treatment objects to list of dicts"""
        if v is None:
            return []
        if isinstance(v, list):
            treatments = []
            for treatment in v:
                if hasattr(treatment, '__dict__'):
                    treatments.append({
                        'id': getattr(treatment, 'id', None),
                        'treatment_name': getattr(treatment, 'treatment_name', None),
                        'status': getattr(treatment, 'status', None),
                        'start_date': getattr(treatment, 'start_date', None),
                        'end_date': getattr(treatment, 'end_date', None),
                    })
                else:
                    treatments.append(treatment)
            return treatments
        return v


class ConditionSummary(BaseModel):
    id: int
    diagnosis: str
    status: str
    severity: Optional[str]
    onset_date: Optional[date]
    end_date: Optional[date]
    icd10_code: Optional[str]
    snomed_code: Optional[str]
    code_description: Optional[str]
    patient_name: Optional[str] = None
    practitioner_name: Optional[str] = None

    class Config:
        from_attributes = True


class ConditionDropdownOption(BaseModel):
    """Minimal condition data for dropdown selections in forms."""

    id: int
    diagnosis: str
    status: str
    severity: Optional[str] = None
    onset_date: Optional[date] = None

    class Config:
        from_attributes = True


# Condition - Medication Relationship Schemas

class ConditionMedicationBase(BaseModel):
    """Base schema for condition medication relationship"""
    
    condition_id: int
    medication_id: int
    relevance_note: Optional[str] = None

    @field_validator("relevance_note")
    @classmethod
    def validate_relevance_note(cls, v):
        """Validate relevance note"""
        if v and len(v.strip()) > 500:
            raise ValueError("Relevance note must be less than 500 characters")
        return v.strip() if v else None


class ConditionMedicationCreate(BaseModel):
    """Schema for creating a condition medication relationship"""
    
    medication_id: int
    relevance_note: Optional[str] = None
    condition_id: Optional[int] = None  # Will be set from URL path parameter

    @field_validator("relevance_note")
    @classmethod
    def validate_relevance_note(cls, v):
        """Validate relevance note"""
        if v and len(v.strip()) > 500:
            raise ValueError("Relevance note must be less than 500 characters")
        return v.strip() if v else None


class ConditionMedicationUpdate(BaseModel):
    """Schema for updating a condition medication relationship"""
    
    relevance_note: Optional[str] = None

    @field_validator("relevance_note")
    @classmethod
    def validate_relevance_note(cls, v):
        """Validate relevance note"""
        if v and len(v.strip()) > 500:
            raise ValueError("Relevance note must be less than 500 characters")
        return v.strip() if v else None


class ConditionMedicationResponse(ConditionMedicationBase):
    """Schema for condition medication relationship response"""
    
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConditionMedicationWithDetails(ConditionMedicationResponse):
    """Schema for condition medication relationship with medication details"""
    
    medication: Optional[dict] = None  # Will contain medication details

    model_config = {"from_attributes": True}
