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
from app.crud.immunization import immunization
from app.models.activity_log import EntityType
from app.schemas.immunization import (
    ImmunizationCreate,
    ImmunizationResponse,
    ImmunizationUpdate,
    ImmunizationWithRelations,
)

router = APIRouter()

# Custom search endpoint with vaccine name filtering (preserves original functionality)
@router.get("/search", response_model=List[ImmunizationResponse])
def search_immunizations(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    vaccine_name: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Search immunizations with filtering by vaccine name."""
    
    # Filter immunizations by the target patient_id
    if vaccine_name:
        immunizations = immunization.get_by_vaccine(
            db, vaccine_name=vaccine_name, patient_id=target_patient_id
        )
    else:
        immunizations = immunization.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    return immunizations

# Add standard CRUD endpoints AFTER custom endpoints to avoid conflicts  
# The GET /{entity_id} will include practitioner relations per the response schema
add_standard_endpoints(
    router,
    crud_obj=immunization,
    entity_type=EntityType.IMMUNIZATION,
    entity_name="Immunization",
    create_schema=ImmunizationCreate,
    update_schema=ImmunizationUpdate,
    response_schema=ImmunizationResponse,
    response_with_relations_schema=ImmunizationWithRelations,
)


@router.get("/patient/{patient_id}/recent", response_model=List[ImmunizationResponse])
def get_recent_immunizations(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    days: int = Query(default=365, ge=1, le=3650),
) -> Any:
    """Get recent immunizations for a patient within specified days."""
    immunizations = immunization.get_recent_immunizations(
        db, patient_id=patient_id, days=days
    )
    return immunizations


@router.get("/patient/{patient_id}/booster-check/{vaccine_name}")
def check_booster_due(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    vaccine_name: str,
    months_interval: int = Query(default=12, ge=1, le=120),
) -> Any:
    """Check if a patient is due for a booster shot."""
    is_due = immunization.get_due_for_booster(
        db,
        patient_id=patient_id,
        vaccine_name=vaccine_name,
        months_interval=months_interval,
    )
    return {
        "patient_id": patient_id,
        "vaccine_name": vaccine_name,
        "booster_due": is_due,
    }


@router.get(
    "/patient/{patient_id}/immunizations/", response_model=List[ImmunizationResponse]
)
def get_patient_immunizations(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """Get all immunizations for a specific patient."""
    immunizations = immunization.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return immunizations
