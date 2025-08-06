from datetime import date, datetime
from typing import Optional, List, ClassVar
from pydantic import BaseModel, Field, validator


class DateValidationMixin:
    """
    Mixin for common date validation patterns.
    Validates that dates are not in the future and end dates are after start dates.
    """
    
    @validator("onset_date", "start_date", "end_date", "diagnosis_date", 
               "administration_date", "collection_date", check_fields=False)
    def validate_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v
    
    @validator("end_date", check_fields=False)
    def validate_end_after_start(cls, v, values):
        if v and "start_date" in values and values["start_date"] and v < values["start_date"]:
            raise ValueError("End date cannot be before start date")
        return v


class StatusValidationMixin:
    """
    Mixin for status field validation.
    Can be customized by setting VALID_STATUSES class attribute.
    """
    
    VALID_STATUSES: ClassVar[List[str]] = ["active", "inactive", "resolved", "pending"]
    
    @validator("status", check_fields=False)
    def validate_status(cls, v):
        if v and v.lower() not in cls.VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(cls.VALID_STATUSES)}")
        return v.lower() if v else v


class SeverityValidationMixin:
    """
    Mixin for severity field validation.
    Can be customized by setting VALID_SEVERITIES class attribute.
    """
    
    VALID_SEVERITIES: ClassVar[List[str]] = ["mild", "moderate", "severe"]
    
    @validator("severity", check_fields=False)
    def validate_severity(cls, v):
        if v and v.lower() not in cls.VALID_SEVERITIES:
            raise ValueError(f"Severity must be one of: {', '.join(cls.VALID_SEVERITIES)}")
        return v.lower() if v else v


class PatientOwnedBase(BaseModel):
    """Base schema for entities owned by a patient."""
    patient_id: int = Field(..., gt=0, description="ID of the patient who owns this record")


class TimestampedBase(BaseModel):
    """Base schema for entities with timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SoftDeleteBase(BaseModel):
    """Base schema for entities that support soft delete."""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)


class AuditableBase(TimestampedBase):
    """Base schema for entities with full audit trail."""
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    version: int = Field(default=1, ge=1)


# Composite base schemas
class PatientOwnedTimestampedBase(PatientOwnedBase, TimestampedBase):
    """Base for patient-owned entities with timestamps."""
    pass


class FullAuditBase(PatientOwnedBase, AuditableBase, SoftDeleteBase):
    """Base for entities with full audit capabilities."""
    pass


class MedicalRecordBase(PatientOwnedBase, DateValidationMixin, StatusValidationMixin):
    """
    Base schema for medical records with common fields and validation.
    Includes patient ownership, date validation, and status validation.
    """
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    status: str = Field(default="active", description="Status")


class ClinicalRecordBase(MedicalRecordBase, TimestampedBase):
    """
    Base schema for clinical records that need timestamps.
    Extends medical records with audit timestamps.
    """
    pass