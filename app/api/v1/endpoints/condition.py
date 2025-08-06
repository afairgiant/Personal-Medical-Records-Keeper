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
)
from app.crud.condition import condition, condition_medication
from app.crud.medication import medication as medication_crud
from app.models.activity_log import EntityType
from app.models.models import User
from app.schemas.condition import (
    ConditionCreate,
    ConditionDropdownOption,
    ConditionResponse,
    ConditionUpdate,
    ConditionWithRelations,
    ConditionMedicationCreate,
    ConditionMedicationResponse,
    ConditionMedicationUpdate,
    ConditionMedicationWithDetails,
)

router = APIRouter()


# Add standard CREATE endpoint
@router.post("/", response_model=ConditionResponse)
def create_condition(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    obj_in: ConditionCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Create new condition record."""
    return handle_create_with_logging(
        db=db, crud_obj=condition, obj_in=obj_in,
        entity_type=EntityType.CONDITION, user_id=current_user_id,
        entity_name="Condition", request=request
    )


# Custom LIST endpoint with filtering (preserve original behavior)
@router.get("/", response_model=List[ConditionResponse])
def read_conditions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    status: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """
    Retrieve conditions for the current user or accessible patient.
    Includes custom filtering by status.
    """
    
    # Filter conditions by the verified accessible patient_id
    if status:
        conditions = condition.get_by_status(
            db, status=status, patient_id=target_patient_id
        )
    else:
        conditions = condition.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    return conditions


# Custom GET by ID endpoint (preserve condition relations)
@router.get("/{condition_id}", response_model=ConditionWithRelations)
def read_condition(
    *,
    db: Session = Depends(deps.get_db),
    condition_id: int,
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """
    Get condition by ID with related information - includes patient/practitioner relations.
    """
    # Get condition and verify it belongs to the user
    condition_obj = condition.get_with_relations(
        db=db,
        record_id=condition_id,
        relations=["patient", "practitioner", "treatments"],
    )
    handle_not_found(condition_obj, "Condition")
    verify_patient_ownership(condition_obj, current_user_patient_id, "condition")
    return condition_obj


# Add standard UPDATE endpoint
@router.put("/{condition_id}", response_model=ConditionResponse)
def update_condition(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    condition_id: int,
    obj_in: ConditionUpdate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Update a condition record."""
    return handle_update_with_logging(
        db=db, crud_obj=condition, entity_id=condition_id, obj_in=obj_in,
        entity_type=EntityType.CONDITION, user_id=current_user_id,
        entity_name="Condition", request=request
    )


# Add standard DELETE endpoint
@router.delete("/{condition_id}")
def delete_condition(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    condition_id: int,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Delete a condition record."""
    return handle_delete_with_logging(
        db=db, crud_obj=condition, entity_id=condition_id,
        entity_type=EntityType.CONDITION, user_id=current_user_id,
        entity_name="Condition", request=request
    )


@router.get("/dropdown", response_model=List[ConditionDropdownOption])
def get_conditions_for_dropdown(
    *,
    db: Session = Depends(deps.get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
    active_only: bool = Query(False, description="Only return active conditions"),
) -> Any:
    """Get conditions formatted for dropdown selection in forms."""
    if active_only:
        conditions = condition.get_active_conditions(
            db, patient_id=current_user_patient_id
        )
    else:
        conditions = condition.get_by_patient(db, patient_id=current_user_patient_id)

    return conditions


# Simple condition medications endpoint
@router.get("/condition-medications/{condition_id}")
def get_condition_medications(
    condition_id: int, 
    db: Session = Depends(deps.get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
):
    """Simple endpoint to get medications for a condition."""
    try:
        # Verify condition exists and belongs to the current user
        db_condition = condition.get(db, id=condition_id)
        if not db_condition:
            raise HTTPException(
                status_code=404,
                detail=f"Condition with ID {condition_id} not found"
            )
        
        # Verify condition belongs to current user
        if db_condition.patient_id != current_user_patient_id:
            raise HTTPException(
                status_code=404,
                detail="Condition not found"
            )
            
        relationships = condition_medication.get_by_condition(db, condition_id=condition_id)
        return [{
            "id": rel.id, 
            "medication_id": rel.medication_id, 
            "condition_id": rel.condition_id,
            "relevance_note": rel.relevance_note,
            "created_at": rel.created_at,
            "updated_at": rel.updated_at
        } for rel in relationships]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error and return a generic error message
        from app.core.logging_config import get_logger
        logger = get_logger(__name__, "app")
        logger.error(f"Error getting condition medications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving condition medications"
        )


@router.post("/{condition_id}/medications", response_model=ConditionMedicationResponse)
def create_condition_medication(
    *,
    condition_id: int,
    medication_in: ConditionMedicationCreate,
    db: Session = Depends(deps.get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Create a new condition medication relationship."""
    try:
        # Verify condition exists and belongs to the current user
        db_condition = condition.get(db, id=condition_id)
        if not db_condition:
            raise HTTPException(
                status_code=404,
                detail=f"Condition with ID {condition_id} not found"
            )
        
        # Verify condition belongs to current user
        if db_condition.patient_id != current_user_patient_id:
            raise HTTPException(
                status_code=404,
                detail="Condition not found"
            )
        
        # Verify medication exists and belongs to the same patient
        db_medication = medication_crud.get(db, id=medication_in.medication_id)
        if not db_medication:
            raise HTTPException(
                status_code=404,
                detail=f"Medication with ID {medication_in.medication_id} not found"
            )
        
        # Ensure medication belongs to the same patient as the condition
        if db_medication.patient_id != current_user_patient_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot link medication that doesn't belong to the same patient"
            )
        
        # Check if relationship already exists
        existing = condition_medication.get_by_condition_and_medication(
            db, condition_id=condition_id, medication_id=medication_in.medication_id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Relationship between this condition and medication already exists"
            )
        
        # Set condition_id and create relationship
        medication_in.condition_id = condition_id
        
        # Create the relationship
        relationship = condition_medication.create(db, obj_in=medication_in)
        return relationship
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error and return a generic error message
        from app.core.logging_config import get_logger
        logger = get_logger(__name__, "app")
        logger.error(f"Error creating condition medication relationship: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the condition medication relationship"
        )


@router.put("/{condition_id}/medications/{relationship_id}", response_model=ConditionMedicationResponse)
def update_condition_medication(
    *,
    condition_id: int,
    relationship_id: int,
    medication_in: ConditionMedicationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Update a condition medication relationship."""
    # Verify condition exists and user has access to it
    db_condition = condition.get(db, id=condition_id)
    handle_not_found(db_condition, "Condition")
    
    # Verify access using multi-patient system
    from app.services.patient_access import PatientAccessService
    from app.models.models import Patient
    
    patient_record = db.query(Patient).filter(Patient.id == db_condition.patient_id).first()
    if not patient_record:
        handle_not_found(None, "Patient")
        
    access_service = PatientAccessService(db)
    if not access_service.can_access_patient(current_user, patient_record, "edit"):
        handle_not_found(None, "Condition")
    
    # Get the relationship
    relationship = condition_medication.get(db, id=relationship_id)
    handle_not_found(relationship, "Condition medication relationship")
    
    # Verify the relationship belongs to the specified condition
    if relationship.condition_id != condition_id:
        raise HTTPException(
            status_code=400,
            detail="Relationship does not belong to the specified condition"
        )
    
    # Update the relationship
    updated_relationship = condition_medication.update(db, db_obj=relationship, obj_in=medication_in)
    return updated_relationship


@router.delete("/{condition_id}/medications/{relationship_id}")
def delete_condition_medication(
    *,
    condition_id: int,
    relationship_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Delete a condition medication relationship."""
    # Verify condition exists and user has access to it
    db_condition = condition.get(db, id=condition_id)
    handle_not_found(db_condition, "Condition")
    
    # Verify access using multi-patient system
    from app.services.patient_access import PatientAccessService
    from app.models.models import Patient
    
    patient_record = db.query(Patient).filter(Patient.id == db_condition.patient_id).first()
    if not patient_record:
        handle_not_found(None, "Patient")
        
    access_service = PatientAccessService(db)
    if not access_service.can_access_patient(current_user, patient_record, "edit"):
        handle_not_found(None, "Condition")
    
    # Get the relationship
    relationship = condition_medication.get(db, id=relationship_id)
    handle_not_found(relationship, "Condition medication relationship")
    
    # Verify the relationship belongs to the specified condition
    if relationship.condition_id != condition_id:
        raise HTTPException(
            status_code=400,
            detail="Relationship does not belong to the specified condition"
        )
    
    # Delete the relationship
    condition_medication.delete(db, id=relationship_id)
    return {"message": "Condition medication relationship deleted successfully"}


@router.get("/patient/{patient_id}/active", response_model=List[ConditionResponse])
def get_active_conditions(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """Get all active conditions for a patient."""
    conditions = condition.get_active_conditions(db, patient_id=patient_id)
    return conditions


@router.get(
    "/patients/{patient_id}/conditions/", response_model=List[ConditionResponse]
)
def get_patient_conditions(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """Get all conditions for a specific patient."""
    conditions = condition.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return conditions


# Medication-focused endpoints (for showing conditions on medication view)

@router.get("/medication/{medication_id}/conditions", response_model=List[ConditionMedicationWithDetails])
def get_medication_conditions(
    *,
    medication_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all condition relationships for a specific medication."""
    # Verify medication exists and user has access to it
    db_medication = medication_crud.get(db, id=medication_id)
    handle_not_found(db_medication, "Medication")
    
    # Verify access using multi-patient system
    from app.services.patient_access import PatientAccessService
    from app.models.models import Patient
    
    patient_record = db.query(Patient).filter(Patient.id == db_medication.patient_id).first()
    if not patient_record:
        handle_not_found(None, "Patient")
        
    access_service = PatientAccessService(db)
    if not access_service.can_access_patient(current_user, patient_record, "view"):
        handle_not_found(None, "Medication")
    
    # Get condition relationships
    relationships = condition_medication.get_by_medication(db, medication_id=medication_id)
    
    # Enhance with condition details
    enhanced_relationships = []
    for rel in relationships:
        condition_obj = condition.get(db, id=rel.condition_id)
        # Verify the condition belongs to the same patient as the medication
        if condition_obj and condition_obj.patient_id != db_medication.patient_id:
            condition_obj = None  # Don't include conditions from other patients
            
        enhanced_relationships.append({
            "id": rel.id,
            "condition_id": rel.condition_id,
            "medication_id": rel.medication_id,
            "relevance_note": rel.relevance_note,
            "created_at": rel.created_at,
            "updated_at": rel.updated_at,
            "condition": {
                "id": condition_obj.id,
                "diagnosis": condition_obj.diagnosis,
                "status": condition_obj.status,
                "severity": condition_obj.severity,
            } if condition_obj else None
        })
    
    return enhanced_relationships
