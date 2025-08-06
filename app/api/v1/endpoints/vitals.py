from datetime import datetime
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
from app.crud.vitals import vitals
from app.models.activity_log import EntityType
from app.schemas.vitals import VitalsCreate, VitalsResponse, VitalsStats, VitalsUpdate

router = APIRouter()

# Add standard CRUD endpoints
add_standard_endpoints(
    router,
    crud_obj=vitals,
    entity_type=EntityType.VITALS,
    entity_name="Vitals",
    create_schema=VitalsCreate,
    update_schema=VitalsUpdate,
    response_schema=VitalsResponse,
    response_with_relations_schema=VitalsResponse,  # No separate with_relations schema
)

# Override the standard create endpoint to use BMI calculation
@router.post("/", response_model=VitalsResponse)
def create_vitals(
    *,
    vitals_in: VitalsCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new vitals reading."""
    # Use create_with_bmi to automatically calculate BMI if weight and height provided
    vitals_obj = vitals.create_with_bmi(db=db, obj_in=vitals_in)

    # Log the creation activity
    from app.api.activity_logging import log_create

    log_create(
        db=db,
        entity_type=EntityType.VITALS,
        entity_obj=vitals_obj,
        user_id=current_user_id,
        request=request,
    )

    return vitals_obj

# Override the standard update endpoint to handle BMI recalculation
@router.put("/{vitals_id}", response_model=VitalsResponse)
def update_vitals(
    *,
    vitals_id: int,
    vitals_in: VitalsUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update vitals reading."""
    # Get existing vitals
    vitals_obj = vitals.get(db=db, id=vitals_id)
    handle_not_found(vitals_obj, "Vitals reading")
    assert vitals_obj is not None  # Type checker hint - handle_not_found raises if None

    # If weight and height are being updated, recalculate BMI
    update_data = vitals_in.dict(exclude_unset=True)
    current_weight = update_data.get("weight", vitals_obj.weight)
    current_height = update_data.get("height", vitals_obj.height)

    if current_weight and current_height:
        bmi = vitals.calculate_bmi(current_weight, current_height)
        update_data["bmi"] = bmi

    updated_vitals = vitals.update(db=db, db_obj=vitals_obj, obj_in=update_data)

    # Log the update activity
    from app.api.activity_logging import log_update

    log_update(
        db=db,
        entity_type=EntityType.VITALS,
        entity_obj=updated_vitals,
        user_id=current_user_id,
        request=request,
    )

    return updated_vitals

# Override the standard get endpoint to include practitioner relations
@router.get("/{vitals_id}", response_model=VitalsResponse)
def read_vitals_by_id(
    *,
    db: Session = Depends(deps.get_db),
    vitals_id: int,
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Get vitals reading by ID with related information - only allows access to user's own vitals."""
    vitals_obj = vitals.get_with_relations(
        db=db, record_id=vitals_id, relations=["patient", "practitioner"]
    )
    handle_not_found(vitals_obj, "Vitals reading")
    verify_patient_ownership(vitals_obj, current_user_patient_id, "vitals")
    return vitals_obj

# Custom stats endpoint (preserve existing functionality)
@router.get("/stats", response_model=VitalsStats)
def read_current_user_vitals_stats(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: Optional[int] = Query(None, description="Patient ID for Phase 1 patient switching"),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Get vitals statistics for the current user or specified patient (Phase 1 support)."""
    
    # Phase 1 support: Use patient_id if provided, otherwise fall back to user's own patient
    if patient_id is not None:
        target_patient_id = patient_id
    else:
        target_patient_id = deps.get_current_user_patient_id(db, current_user_id)
    
    stats = vitals.get_vitals_stats(db=db, patient_id=target_patient_id)
    return stats


@router.get("/patient/{patient_id}", response_model=List[VitalsResponse])
def read_patient_vitals(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    vital_type: Optional[str] = Query(
        None,
        description="Filter by vital type: blood_pressure, heart_rate, temperature, weight, oxygen_saturation, blood_glucose",
    ),
    days: Optional[int] = Query(None, description="Get readings from last N days"),
) -> Any:
    """Get all vitals readings for a specific patient."""
    if days:
        # Get recent readings
        vitals_list = vitals.get_recent_readings(
            db=db, patient_id=patient_id, days=days
        )
    elif vital_type:
        # Get by specific vital type
        vitals_list = vitals.get_by_vital_type(
            db=db, patient_id=patient_id, vital_type=vital_type, skip=skip, limit=limit
        )
    else:
        # Get all readings for patient
        vitals_list = vitals.get_by_patient(
            db=db, patient_id=patient_id, skip=skip, limit=limit
        )

    return vitals_list


@router.get("/patient/{patient_id}/latest", response_model=VitalsResponse)
def read_patient_latest_vitals(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """Get the most recent vitals reading for a patient."""
    latest_vitals = vitals.get_latest_by_patient(db=db, patient_id=patient_id)
    if not latest_vitals:
        raise HTTPException(
            status_code=404, detail="No vitals readings found for this patient"
        )
    return latest_vitals


@router.get("/patient/{patient_id}/stats", response_model=VitalsStats)
def read_patient_vitals_stats(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """Get vitals statistics for a patient."""
    stats = vitals.get_vitals_stats(db=db, patient_id=patient_id)
    return stats


@router.get("/patient/{patient_id}/date-range", response_model=List[VitalsResponse])
def read_patient_vitals_date_range(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    start_date: datetime = Query(..., description="Start date for the range"),
    end_date: datetime = Query(..., description="End date for the range"),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """Get vitals readings for a patient within a specific date range."""
    vitals_list = vitals.get_by_patient_date_range(
        db=db,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return vitals_list


@router.post("/patient/{patient_id}/vitals/", response_model=VitalsResponse)
def create_patient_vitals(
    *,
    vitals_in: VitalsCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create a new vitals reading for a specific patient."""
    # Ensure the patient_id in the URL matches the one in the request body
    if vitals_in.patient_id != patient_id:
        raise HTTPException(
            status_code=400,
            detail="Patient ID in URL does not match patient ID in request body",
        )

    return create_vitals(
        vitals_in=vitals_in, request=request, db=db, current_user_id=current_user_id
    )
