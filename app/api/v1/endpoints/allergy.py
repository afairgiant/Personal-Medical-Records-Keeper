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

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

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

# Add standard CRUD endpoints AFTER custom endpoints to avoid conflicts
# This will create: POST /, GET /{entity_id}, PUT /{entity_id}, DELETE /{entity_id}
add_standard_endpoints(
    router,
    crud_obj=allergy,
    entity_type=EntityType.ALLERGY,
    entity_name="Allergy",
    create_schema=AllergyCreate,
    update_schema=AllergyUpdate,
    response_schema=AllergyResponse,
    response_with_relations_schema=AllergyWithRelations,
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
