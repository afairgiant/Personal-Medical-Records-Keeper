from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    handle_create_with_logging,
    handle_delete_with_logging,
    handle_not_found,
    handle_update_with_logging,
    add_standard_endpoints,
)
from app.crud.practitioner import practitioner
from app.models.activity_log import EntityType
from app.schemas.practitioner import (
    Practitioner,
    PractitionerCreate,
    PractitionerUpdate,
)

router = APIRouter()

# NOTE: Practitioner endpoints are global (not patient-specific) so we use get_multi instead of get_by_patient

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# Custom list endpoint with specialty filtering
@router.get("/", response_model=List[Practitioner])
def read_practitioners(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    specialty: Optional[str] = Query(None),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Retrieve practitioners with optional filtering by specialty."""
    if specialty:
        practitioners = practitioner.get_by_specialty(
            db, specialty=specialty, skip=skip, limit=limit
        )
    else:
        practitioners = practitioner.get_multi(db, skip=skip, limit=limit)
    return practitioners

# Search endpoint (before standard endpoints)
@router.get("/search/by-name", response_model=List[Practitioner])
def search_practitioners_by_name(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Query(..., min_length=2),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Search practitioners by name."""
    practitioners = practitioner.search_by_name(db, name=name)
    return practitioners

# Custom GET by ID with extensive relations
@router.get("/{practitioner_id}", response_model=Practitioner)
def read_practitioner(
    *,
    db: Session = Depends(deps.get_db),
    practitioner_id: int,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Get practitioner by ID with related information."""
    practitioner_obj = practitioner.get_with_relations(
        db=db, record_id=practitioner_id, relations=["patients", "conditions", "treatments", "medications", "procedures", "encounters", "lab_results", "immunizations", "vitals"]
    )
    handle_not_found(practitioner_obj, "Practitioner")
    return practitioner_obj

# NOTE: Cannot use standard endpoints due to global nature (not patient-specific)
# and need for extensive relation loading in GET by ID
# Keeping all endpoints custom

@router.post("/", response_model=Practitioner)
def create_practitioner(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    obj_in: PractitionerCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new practitioner record."""
    return handle_create_with_logging(
        db=db, crud_obj=practitioner, obj_in=obj_in,
        entity_type=EntityType.PRACTITIONER, user_id=current_user_id,
        entity_name="Practitioner", request=request
    )

@router.put("/{practitioner_id}", response_model=Practitioner)
def update_practitioner(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    practitioner_id: int,
    obj_in: PractitionerUpdate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update a practitioner record."""
    return handle_update_with_logging(
        db=db, crud_obj=practitioner, entity_id=practitioner_id, obj_in=obj_in,
        entity_type=EntityType.PRACTITIONER, user_id=current_user_id,
        entity_name="Practitioner", request=request
    )

@router.delete("/{practitioner_id}")
def delete_practitioner(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    practitioner_id: int,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Delete a practitioner record."""
    return handle_delete_with_logging(
        db=db, crud_obj=practitioner, entity_id=practitioner_id,
        entity_type=EntityType.PRACTITIONER, user_id=current_user_id,
        entity_name="Practitioner", request=request
    )

# NOTE: Practitioner endpoints are global (not patient-specific) and require extensive relation loading
# Cannot use add_standard_endpoints() due to global nature and custom filtering/search needs
