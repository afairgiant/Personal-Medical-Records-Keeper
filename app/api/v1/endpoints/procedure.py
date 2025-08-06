from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    handle_not_found,
    verify_patient_ownership,
    add_standard_endpoints,
)
from app.crud.procedure import procedure
from app.models.activity_log import EntityType
from app.schemas.procedure import (
    ProcedureCreate,
    ProcedureResponse,
    ProcedureUpdate,
    ProcedureWithRelations,
)

router = APIRouter()

# Add standard CRUD endpoints
add_standard_endpoints(
    router,
    crud_obj=procedure,
    entity_type=EntityType.PROCEDURE,
    entity_name="Procedure",
    create_schema=ProcedureCreate,
    update_schema=ProcedureUpdate,
    response_schema=ProcedureResponse,
    response_with_relations_schema=ProcedureWithRelations,
)

# Override the standard list endpoint to support custom filtering
@router.get("/", response_model=List[ProcedureResponse])
def read_procedures(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    practitioner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """
    Retrieve procedures for the current user or accessible patient.
    """
    
    # Filter procedures by the target patient_id
    if status:
        procedures = procedure.get_by_status(
            db, status=status, patient_id=target_patient_id
        )
    elif practitioner_id:
        procedures = procedure.get_by_practitioner(
            db,
            practitioner_id=practitioner_id,
            patient_id=target_patient_id,
            skip=skip,
            limit=limit,
        )
    else:
        procedures = procedure.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    return procedures

# Override the standard get endpoint to include all necessary relations
@router.get("/{procedure_id}", response_model=ProcedureWithRelations)
def read_procedure(
    *,
    db: Session = Depends(deps.get_db),
    procedure_id: int,
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """
    Get procedure by ID with related information - only allows access to user's own procedures.
    """
    procedure_obj = procedure.get_with_relations(
        db=db, record_id=procedure_id, relations=["patient", "practitioner", "condition"]
    )
    handle_not_found(procedure_obj, "Procedure")
    verify_patient_ownership(procedure_obj, current_user_patient_id, "procedure")
    return procedure_obj


@router.get("/scheduled", response_model=List[ProcedureResponse])
def get_scheduled_procedures(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: Optional[int] = Query(None),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """
    Get all scheduled procedures, optionally filtered by patient.
    """
    procedures = procedure.get_scheduled(db, patient_id=patient_id)
    return procedures


@router.get("/patient/{patient_id}/recent", response_model=List[ProcedureResponse])
def get_recent_procedures(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    days: int = Query(default=90, ge=1, le=365),
) -> Any:
    """
    Get recent procedures for a patient within specified days.
    """
    procedures = procedure.get_recent(db, patient_id=patient_id, days=days)
    return procedures


@router.get(
    "/patients/{patient_id}/procedures/", response_model=List[ProcedureResponse]
)
def get_patient_procedures(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """
    Get all procedures for a specific patient.
    """
    procedures = procedure.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return procedures
