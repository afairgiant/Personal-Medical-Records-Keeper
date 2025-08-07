from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    handle_not_found,
    verify_patient_ownership,
    add_standard_endpoints,
)
from app.crud.emergency_contact import emergency_contact
from app.models.activity_log import EntityType
from app.models.models import EmergencyContact
from app.schemas.emergency_contact import (
    EmergencyContactCreate,
    EmergencyContactResponse,
    EmergencyContactUpdate,
    EmergencyContactWithRelations,
)

router = APIRouter()

# Custom endpoints BEFORE standard endpoints to avoid path conflicts

# Custom create endpoint will be handled by add_standard_endpoints()

# Custom list endpoint will be handled by add_standard_endpoints()

# Standard GET, PUT, DELETE endpoints will be handled by add_standard_endpoints()


# Add standard CRUD endpoints AFTER custom endpoints to avoid conflicts  
# This will create: POST /, GET /, GET /{entity_id}, PUT /{entity_id}, DELETE /{entity_id}
add_standard_endpoints(
    router,
    crud_obj=emergency_contact,
    entity_type=EntityType.EMERGENCY_CONTACT,
    entity_name="EmergencyContact",
    create_schema=EmergencyContactCreate,
    update_schema=EmergencyContactUpdate,
    response_schema=EmergencyContactResponse,
    response_with_relations_schema=EmergencyContactWithRelations,
)


@router.get("/patient/{patient_id}/primary", response_model=EmergencyContactResponse)
def get_primary_emergency_contact(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int = Depends(deps.verify_patient_access),
) -> Any:
    """Get the primary emergency contact for a patient."""
    primary_contact = emergency_contact.get_primary_contact(db, patient_id=patient_id)
    if not primary_contact:
        raise HTTPException(
            status_code=404, detail="Primary Emergency Contact not found"
        )
    return primary_contact


@router.post(
    "/{emergency_contact_id}/set-primary", response_model=EmergencyContactResponse
)
def set_primary_emergency_contact(
    *,
    db: Session = Depends(deps.get_db),
    emergency_contact_id: int,
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Set an emergency contact as the primary contact."""
    # Verify the contact belongs to the current user
    contact_obj = emergency_contact.get(db, id=emergency_contact_id)
    if not contact_obj:
        raise HTTPException(status_code=404, detail="Emergency Contact not found")

    # Security check: ensure the contact belongs to the current user
    deps.verify_patient_record_access(
        getattr(contact_obj, "patient_id"), current_user_patient_id, "emergency contact"
    )

    # Set as primary
    updated_contact = emergency_contact.set_primary_contact(
        db, contact_id=emergency_contact_id, patient_id=current_user_patient_id
    )
    return updated_contact
