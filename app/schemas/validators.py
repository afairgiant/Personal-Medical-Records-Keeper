from datetime import date
from typing import List
from pydantic import validator, Field

def validate_date_not_future(cls, v):
    """
    Common validator for dates that cannot be in the future.
    
    Args:
        cls: The Pydantic model class
        v: The date value to validate
        
    Returns:
        The validated date
        
    Raises:
        ValueError: If date is in the future
    """
    if v and v > date.today():
        raise ValueError("Date cannot be in the future")
    return v

def validate_status(valid_statuses: List[str]):
    """
    Create a status validator for specific valid statuses.
    
    Args:
        valid_statuses: List of valid status values
        
    Returns:
        A validator function
    """
    def status_validator(cls, v):
        if v and v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower() if v else v
    return validator("status", allow_reuse=True)(status_validator)

def validate_severity(valid_severities: List[str]):
    """
    Create a severity validator for specific valid severities.
    
    Args:
        valid_severities: List of valid severity values
        
    Returns:
        A validator function
    """
    def severity_validator(cls, v):
        if v and v.lower() not in valid_severities:
            raise ValueError(f"Severity must be one of: {', '.join(valid_severities)}")
        return v.lower() if v else v
    return validator("severity", allow_reuse=True)(severity_validator)

def validate_end_after_start(cls, v, values):
    """
    Common validator to ensure end date is after start date.
    
    Args:
        cls: The Pydantic model class
        v: The end date value
        values: Dictionary of previously validated values
        
    Returns:
        The validated end date
        
    Raises:
        ValueError: If end date is before start date
    """
    if v and "start_date" in values and values["start_date"] and v < values["start_date"]:
        raise ValueError("End date cannot be before start date")
    return v

# Common validators that can be reused
validate_onset_date = validator("onset_date", "start_date", "end_date", 
                               "diagnosis_date", "administration_date", "collection_date", 
                               allow_reuse=True)(validate_date_not_future)

validate_end_date = validator("end_date", allow_reuse=True)(validate_end_after_start)

# Common field patterns
# Standard patient_id field
PATIENT_ID_FIELD = Field(..., gt=0, description="ID of the patient")

# Standard notes field  
NOTES_FIELD = Field(None, max_length=1000, description="Additional notes")

# Standard status field
STATUS_FIELD = Field(default="active", description="Status")

# Common severity field options
ALLERGY_SEVERITIES = ["mild", "moderate", "severe", "life-threatening"]
CONDITION_SEVERITIES = ["mild", "moderate", "severe", "critical"]

# Common status field options
ACTIVE_STATUSES = ["active", "inactive", "resolved"]
EXTENDED_STATUSES = ["active", "inactive", "resolved", "unconfirmed", "pending"]