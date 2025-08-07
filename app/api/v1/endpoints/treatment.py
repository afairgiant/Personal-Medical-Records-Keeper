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
from app.crud.treatment import treatment
from app.models.activity_log import EntityType
from app.schemas.treatment import (
    TreatmentCreate,
    TreatmentResponse,
    TreatmentUpdate,
    TreatmentWithRelations,
)

router = APIRouter()

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# Custom list endpoint with status and condition_id filtering
@router.get("/search", response_model=List[TreatmentResponse])
def search_treatments(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    condition_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Search treatments with filtering by status or condition_id."""
    
    # Filter treatments by the target patient_id
    if status:
        treatments = treatment.get_by_status(
            db,
            status=status,
            patient_id=target_patient_id,
        )
    elif condition_id:
        treatments = treatment.get_by_condition(
            db,
            condition_id=condition_id,
            patient_id=target_patient_id,
            skip=skip,
            limit=limit,
        )
    else:
        treatments = treatment.get_by_patient(
            db,
            patient_id=target_patient_id,
            skip=skip,
            limit=limit,
        )
    return treatments


# Custom ongoing treatments endpoint (BEFORE standard endpoints)
@router.get("/ongoing", response_model=List[TreatmentResponse])
def get_ongoing_treatments(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: Optional[int] = Query(None),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Get treatments that are currently ongoing."""
    treatments = treatment.get_ongoing(db, patient_id=patient_id)
    return treatments


@router.get("/patient/{patient_id}/active", response_model=List[TreatmentResponse])
def get_active_treatments(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """Get all active treatments for a patient."""
    treatments = treatment.get_active_treatments(db, patient_id=patient_id)
    return treatments



# Add standard CRUD endpoints AFTER custom endpoints
# This creates: POST /, GET /, GET /{entity_id}, PUT /{entity_id}, DELETE /{entity_id}
# The GET /{entity_id} will include condition relations per the response schema
add_standard_endpoints(
    router,
    crud_obj=treatment,
    entity_type=EntityType.TREATMENT,
    entity_name="Treatment",
    create_schema=TreatmentCreate,
    update_schema=TreatmentUpdate,
    response_schema=TreatmentResponse,
    response_with_relations_schema=TreatmentWithRelations,
)


@router.get(
    "/patients/{patient_id}/treatments/", response_model=List[TreatmentResponse]
)
def get_patient_treatments(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """Get all treatments for a specific patient."""
    treatments = treatment.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return treatments
