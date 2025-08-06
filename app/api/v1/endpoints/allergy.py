from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    handle_create_with_logging,
    handle_delete_with_logging,
    handle_not_found,
    handle_update_with_logging,
    verify_patient_ownership,
    add_standard_endpoints,
)
from app.crud.allergy import allergy
from app.models.activity_log import EntityType
from app.schemas.allergy import (
    AllergyCreate,
    AllergyResponse,
    AllergyUpdate,
    AllergyWithRelations,
)

router = APIRouter()

# Add standard CREATE endpoint
@router.post("/", response_model=AllergyResponse)
def create_allergy(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    obj_in: AllergyCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new allergy record."""
    return handle_create_with_logging(
        db=db, crud_obj=allergy, obj_in=obj_in,
        entity_type=EntityType.ALLERGY, user_id=current_user_id,
        entity_name="Allergy", request=request
    )

# Custom LIST endpoint with filtering (preserve original behavior)
@router.get("/", response_model=List[AllergyResponse])
def read_allergies(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    severity: Optional[str] = Query(None),
    allergen: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """
    Retrieve allergies for the current user or accessible patient.
    Includes custom filtering by severity and allergen.
    """
    
    # Filter allergies by the target patient_id
    if severity:
        allergies = allergy.get_by_severity(
            db, severity=severity, patient_id=target_patient_id
        )
    elif allergen:
        allergies = allergy.get_by_allergen(
            db, allergen=allergen, patient_id=target_patient_id
        )
    else:
        allergies = allergy.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    return allergies

# Custom GET by ID endpoint (preserve medication relations)
@router.get("/{allergy_id}", response_model=AllergyWithRelations)
def read_allergy(
    *,
    db: Session = Depends(deps.get_db),
    allergy_id: int,
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """
    Get allergy by ID with related information - includes medication relations.
    """
    # Get allergy and verify it belongs to the user
    allergy_obj = allergy.get_with_relations(
        db=db, record_id=allergy_id, relations=["patient", "medication"]
    )
    handle_not_found(allergy_obj, "Allergy")
    verify_patient_ownership(allergy_obj, current_user_patient_id, "allergy")
    return allergy_obj

# Add standard UPDATE endpoint
@router.put("/{allergy_id}", response_model=AllergyResponse)
def update_allergy(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    allergy_id: int,
    obj_in: AllergyUpdate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update an allergy record."""
    return handle_update_with_logging(
        db=db, crud_obj=allergy, entity_id=allergy_id, obj_in=obj_in,
        entity_type=EntityType.ALLERGY, user_id=current_user_id,
        entity_name="Allergy", request=request
    )

# Add standard DELETE endpoint  
@router.delete("/{allergy_id}")
def delete_allergy(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    allergy_id: int,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Delete an allergy record."""
    return handle_delete_with_logging(
        db=db, crud_obj=allergy, entity_id=allergy_id,
        entity_type=EntityType.ALLERGY, user_id=current_user_id,
        entity_name="Allergy", request=request
    )


@router.get("/patient/{patient_id}/active", response_model=List[AllergyResponse])
def get_active_allergies(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """
    Get all active allergies for a patient.
    """
    allergies = allergy.get_active_allergies(db, patient_id=patient_id)
    return allergies


@router.get("/patient/{patient_id}/critical", response_model=List[AllergyResponse])
def get_critical_allergies(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """
    Get critical (severe and life-threatening) allergies for a patient.
    """
    allergies = allergy.get_critical_allergies(db, patient_id=patient_id)
    return allergies


@router.get("/patient/{patient_id}/check/{allergen}")
def check_allergen_conflict(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    allergen: str,
) -> Any:
    """
    Check if a patient has any active allergies to a specific allergen.
    """
    has_allergy = allergy.check_allergen_conflict(
        db, patient_id=patient_id, allergen=allergen
    )
    return {"patient_id": patient_id, "allergen": allergen, "has_allergy": has_allergy}


@router.get("/patients/{patient_id}/allergies/", response_model=List[AllergyResponse])
def get_patient_allergies(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """
    Get all allergies for a specific patient.
    """
    allergies = allergy.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return allergies
