from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    handle_create_with_logging,
    handle_not_found,
    handle_update_with_logging,
    add_standard_endpoints,
)
from app.crud.pharmacy import pharmacy
from app.models.activity_log import EntityType
from app.schemas.pharmacy import Pharmacy, PharmacyCreate, PharmacyUpdate

router = APIRouter()

# NOTE: Pharmacy endpoints are global (not patient-specific) so we use get_multi instead of get_by_patient

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# NOTE: Cannot use standard endpoints due to global nature and special delete handling
# Keeping all endpoints custom

@router.post("/", response_model=Pharmacy)
def create_pharmacy(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    obj_in: PharmacyCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new pharmacy record."""
    return handle_create_with_logging(
        db=db, crud_obj=pharmacy, obj_in=obj_in,
        entity_type=EntityType.PHARMACY, user_id=current_user_id,
        entity_name="Pharmacy", request=request
    )

# Custom list endpoint for global pharmacies
@router.get("/", response_model=List[Pharmacy])
def read_pharmacies(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Retrieve pharmacies."""
    pharmacies = pharmacy.get_multi(db, skip=skip, limit=limit)
    return pharmacies

@router.get("/{pharmacy_id}", response_model=Pharmacy)
def read_pharmacy(
    *,
    db: Session = Depends(deps.get_db),
    pharmacy_id: int,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Get pharmacy by ID."""
    pharmacy_obj = pharmacy.get(db=db, id=pharmacy_id)
    handle_not_found(pharmacy_obj, "Pharmacy")
    return pharmacy_obj

@router.put("/{pharmacy_id}", response_model=Pharmacy)
def update_pharmacy(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    pharmacy_id: int,
    obj_in: PharmacyUpdate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update a pharmacy record."""
    return handle_update_with_logging(
        db=db, crud_obj=pharmacy, entity_id=pharmacy_id, obj_in=obj_in,
        entity_type=EntityType.PHARMACY, user_id=current_user_id,
        entity_name="Pharmacy", request=request
    )

# Custom delete endpoint to handle medication references
@router.delete("/{pharmacy_id}")
def delete_pharmacy(
    *,
    pharmacy_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Delete a pharmacy."""
    from app.models.models import Medication

    pharmacy_obj = pharmacy.get(db=db, id=pharmacy_id)
    handle_not_found(pharmacy_obj, "Pharmacy")

    # Check how many medications reference this pharmacy
    medication_count = db.query(Medication).filter(Medication.pharmacy_id == pharmacy_id).count()

    # Set pharmacy_id to NULL for all medications that reference this pharmacy
    if medication_count > 0:
        db.query(Medication).filter(Medication.pharmacy_id == pharmacy_id).update(
            {"pharmacy_id": None}
        )
        db.commit()

    # Log the deletion activity BEFORE deleting with custom description
    base_description = (
        f"Deleted pharmacy: {getattr(pharmacy_obj, 'name', 'Unknown pharmacy')}"
    )
    if medication_count > 0:
        description = f"{base_description}. Updated {medication_count} medication(s) to remove pharmacy reference."
    else:
        description = base_description

    from app.api.activity_logging import safe_log_activity
    from app.models.activity_log import ActionType

    safe_log_activity(
        db=db,
        action=ActionType.DELETED,
        entity_type=EntityType.PHARMACY,
        entity_obj=pharmacy_obj,
        user_id=current_user_id,
        description=description,
        request=request,
    )

    # Delete the pharmacy
    pharmacy.delete(db=db, id=pharmacy_id)

    return {"ok": True}

# NOTE: Pharmacy endpoints are global (not patient-specific) and require special delete handling
# Cannot use add_standard_endpoints() due to global nature and medication reference cleanup
