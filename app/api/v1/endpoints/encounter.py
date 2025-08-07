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
from app.crud.encounter import encounter
from app.models.activity_log import EntityType
from app.schemas.encounter import (
    EncounterCreate,
    EncounterResponse,
    EncounterUpdate,
    EncounterWithRelations,
)

router = APIRouter()

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# Custom search endpoint with practitioner_id filtering
@router.get("/search", response_model=List[EncounterResponse])
def search_encounters(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    practitioner_id: Optional[int] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Search encounters with filtering by practitioner_id."""
    
    # Filter encounters by the verified accessible patient_id
    if practitioner_id:
        encounters = encounter.get_by_practitioner(
            db,
            practitioner_id=practitioner_id,
            patient_id=target_patient_id,
            skip=skip,
            limit=limit,
        )
    else:
        encounters = encounter.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    return encounters



# Add standard CRUD endpoints AFTER custom endpoints
# This creates: POST /, GET /, GET /{entity_id}, PUT /{entity_id}, DELETE /{entity_id}
# The GET /{entity_id} will include relations per the response schema
add_standard_endpoints(
    router,
    crud_obj=encounter,
    entity_type=EntityType.ENCOUNTER,
    entity_name="Encounter",
    create_schema=EncounterCreate,
    update_schema=EncounterUpdate,
    response_schema=EncounterResponse,
    response_with_relations_schema=EncounterWithRelations,
)


@router.get("/patient/{patient_id}/recent", response_model=List[EncounterResponse])
def get_recent_encounters(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    days: int = Query(default=30, ge=1, le=365),
) -> Any:
    """Get recent encounters for a patient within specified days."""
    encounters = encounter.get_recent(db, patient_id=patient_id, days=days)
    return encounters


@router.get(
    "/patients/{patient_id}/encounters/", response_model=List[EncounterResponse]
)
def get_patient_encounters(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """Get all encounters for a specific patient."""
    encounters = encounter.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return encounters
