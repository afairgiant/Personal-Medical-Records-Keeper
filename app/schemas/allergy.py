from datetime import date
from typing import Optional, ClassVar, List
from pydantic import BaseModel, Field, validator

from app.schemas.base import (
    PatientOwnedBase,
    DateValidationMixin, 
    StatusValidationMixin,
    SeverityValidationMixin
)


class AllergyBase(PatientOwnedBase, DateValidationMixin, StatusValidationMixin, SeverityValidationMixin):
    """Base schema for allergy records with validation mixins."""
    
    # Define valid severities for allergy-specific validation
    VALID_SEVERITIES: ClassVar[List[str]] = ["mild", "moderate", "severe", "life-threatening"]
    VALID_STATUSES: ClassVar[List[str]] = ["active", "inactive", "resolved", "unconfirmed"]
    
    allergen: str = Field(
        ..., min_length=2, max_length=200, description="Name of the allergen"
    )
    reaction: Optional[str] = Field(
        None, max_length=500, description="Description of the allergic reaction"
    )
    severity: str = Field(..., description="Severity of the allergy")
    onset_date: Optional[date] = Field(
        None, description="Date when the allergy was first identified"
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes about the allergy"
    )
    status: str = Field(default="active", description="Status of the allergy")
    medication_id: Optional[int] = Field(None, gt=0, description="ID of the medication causing this allergy")


class AllergyCreate(AllergyBase):
    pass


class AllergyUpdate(DateValidationMixin, StatusValidationMixin, SeverityValidationMixin, BaseModel):
    """Schema for updating allergy records."""
    
    # Define valid severities for allergy-specific validation
    VALID_SEVERITIES: ClassVar[List[str]] = ["mild", "moderate", "severe", "life-threatening"]
    VALID_STATUSES: ClassVar[List[str]] = ["active", "inactive", "resolved", "unconfirmed"]
    
    allergen: Optional[str] = Field(None, min_length=2, max_length=200)
    reaction: Optional[str] = Field(None, max_length=500)
    severity: Optional[str] = None
    onset_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    medication_id: Optional[int] = Field(None, gt=0)


class AllergyResponse(AllergyBase):
    id: int

    class Config:
        from_attributes = True


class AllergyWithRelations(AllergyResponse):
    patient: Optional[dict] = None
    medication: Optional[dict] = None

    class Config:
        from_attributes = True


class AllergySummary(BaseModel):
    id: int
    allergen: str
    severity: str
    status: str
    onset_date: Optional[date]
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True
