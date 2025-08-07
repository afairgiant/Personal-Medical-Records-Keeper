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
from app.api.activity_logging import log_update
from app.crud.insurance import insurance
from app.models.activity_log import EntityType
from app.models.models import User
from app.schemas.insurance import (
    Insurance,
    InsuranceCreate,
    InsuranceStatusUpdate,
    InsuranceUpdate,
)

router = APIRouter()

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# Filter endpoint with multiple filters (preserves original functionality)
@router.get("/filter", response_model=List[Insurance])
def filter_insurances(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    insurance_type: Optional[str] = Query(None, description="Filter by insurance type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Show only active insurances"),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Filter insurance records for the current patient."""
    
    # Apply filters based on query parameters
    if active_only:
        insurances = insurance.get_active_by_patient(
            db=db, patient_id=target_patient_id
        )
    elif insurance_type:
        insurances = insurance.get_by_type(
            db=db, patient_id=target_patient_id, insurance_type=insurance_type
        )
    elif status:
        insurances = insurance.get_by_status(
            db=db, patient_id=target_patient_id, status=status
        )
    else:
        insurances = insurance.get_by_patient(
            db=db, patient_id=target_patient_id
        )

    # Apply pagination
    return insurances[skip : skip + limit]


# Expiring insurances endpoint (before standard endpoints)
@router.get("/expiring", response_model=List[Insurance])
def get_expiring_insurances(
    *,
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="Days ahead to check for expiration"),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Get insurance records expiring within specified days."""

    return insurance.get_expiring_soon(
        db=db, patient_id=target_patient_id, days=days
    )


# Search endpoint (before standard endpoints)
@router.get("/search", response_model=List[Insurance])
def search_insurances(
    *,
    db: Session = Depends(deps.get_db),
    company: str = Query(..., min_length=1, description="Company name to search for"),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Search insurance records by company name."""

    return insurance.search_by_company(
        db=db, patient_id=target_patient_id, company_name=company
    )


# Custom CREATE endpoint (matches working pattern from medication.py)
@router.post("/", response_model=Insurance)
def create_insurance(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    obj_in: InsuranceCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new insurance record."""
    insurance_obj = handle_create_with_logging(
        db=db, crud_obj=insurance, obj_in=obj_in,
        entity_type=EntityType.INSURANCE, user_id=current_user_id,
        entity_name="Insurance", request=request
    )
    return insurance_obj


# Custom LIST endpoint (matches working pattern)
@router.get("/", response_model=List[Insurance])
def read_insurances(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Retrieve insurance records for the current user or accessible patient."""
    return insurance.get_by_patient(
        db=db, patient_id=target_patient_id, skip=skip, limit=limit
    )


# Custom GET by ID endpoint  
@router.get("/{insurance_id}", response_model=Insurance)
def get_insurance(
    *,
    insurance_id: int,
    db: Session = Depends(deps.get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Get insurance by ID."""
    insurance_obj = insurance.get(db=db, id=insurance_id)
    handle_not_found(insurance_obj, "Insurance")
    verify_patient_ownership(insurance_obj, current_user_patient_id, "insurance")
    return insurance_obj


# Custom UPDATE endpoint
@router.put("/{insurance_id}", response_model=Insurance)
def update_insurance(
    *,
    insurance_id: int,
    obj_in: InsuranceUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Update insurance record."""
    insurance_obj = insurance.get(db=db, id=insurance_id)
    handle_not_found(insurance_obj, "Insurance")
    verify_patient_ownership(insurance_obj, current_user_patient_id, "insurance")
    
    updated_insurance = handle_update_with_logging(
        db=db, crud_obj=insurance, entity_id=insurance_id, obj_in=obj_in,
        entity_type=EntityType.INSURANCE, user_id=current_user_id,
        entity_name="Insurance", request=request
    )
    return updated_insurance


# Custom DELETE endpoint
@router.delete("/{insurance_id}")
def delete_insurance(
    *,
    insurance_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Delete insurance record."""
    insurance_obj = insurance.get(db=db, id=insurance_id)
    handle_not_found(insurance_obj, "Insurance")
    verify_patient_ownership(insurance_obj, current_user_patient_id, "insurance")
    
    return handle_delete_with_logging(
        db=db, crud_obj=insurance, entity_id=insurance_id,
        entity_type=EntityType.INSURANCE, user_id=current_user_id,
        entity_name="Insurance", request=request
    )

@router.patch("/{insurance_id}/status", response_model=Insurance)
def update_insurance_status(
    *,
    insurance_id: int,
    status_update: InsuranceStatusUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update insurance status only."""
    insurance_obj = insurance.get(db=db, id=insurance_id)
    if not insurance_obj:
        handle_not_found(insurance_obj, "Insurance")

    # Verify patient ownership
    current_user_patient_id = deps.get_current_user_patient_id(db=db, current_user_id=current_user_id)
    verify_patient_ownership(
        insurance_obj, current_user_patient_id, "insurance"
    )

    updated_insurance = handle_update_with_logging(
        db=db,
        crud_obj=insurance,
        entity_id=insurance_id,
        obj_in=status_update,
        entity_type=EntityType.INSURANCE,
        user_id=current_user_id,
        entity_name="Insurance",
        request=request,
    )

    return updated_insurance


@router.patch("/{insurance_id}/set-primary", response_model=Insurance)
def set_primary_insurance(
    *,
    insurance_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Set insurance as primary (unsets others of same type)."""
    
    # Verify the insurance exists and belongs to the current patient
    insurance_obj = insurance.get(db=db, id=insurance_id)
    if not insurance_obj:
        handle_not_found(insurance_obj, "Insurance")

    current_user_patient_id = deps.get_current_user_patient_id(db=db, current_user_id=current_user.id)
    verify_patient_ownership(
        insurance_obj, current_user_patient_id, "insurance"
    )

    # Set as primary
    updated_insurance = insurance.set_primary(
        db=db, patient_id=target_patient_id, insurance_id=insurance_id
    )

    if not updated_insurance:
        raise HTTPException(status_code=400, detail="Failed to set insurance as primary")

    # Log the activity
    log_update(
        db=db,
        entity_type=EntityType.INSURANCE,
        entity_obj=updated_insurance,
        user_id=current_user.id,
        request=request,
    )

    return updated_insurance
