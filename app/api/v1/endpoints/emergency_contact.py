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

# Add standard CRUD endpoints
add_standard_endpoints(
    router,
    crud_obj=emergency_contact,
    entity_type=EntityType.EMERGENCY_CONTACT,
    entity_name="Emergency Contact",
    create_schema=EmergencyContactCreate,
    update_schema=EmergencyContactUpdate,
    response_schema=EmergencyContactResponse,
    response_with_relations_schema=EmergencyContactWithRelations,
)

# Override the standard create endpoint to use specialized creation method
@router.post("/", response_model=EmergencyContactResponse)
def create_emergency_contact(
    *,
    request: Request,
    db: Session = Depends(deps.get_db),
    emergency_contact_in: EmergencyContactCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Create new emergency contact."""
    # Use the specialized method that handles patient_id properly
    emergency_contact_obj = emergency_contact.create_for_patient(
        db=db, patient_id=current_user_patient_id, obj_in=emergency_contact_in
    )

    # Log the creation activity using centralized logging
    from app.api.activity_logging import log_create
    log_create(
        db=db,
        entity_type=EntityType.EMERGENCY_CONTACT,
        entity_obj=emergency_contact_obj,
        user_id=current_user_id,
        request=request,
    )

    return emergency_contact_obj

# Override the standard list endpoint to support custom filtering and ordering
@router.get("/", response_model=List[EmergencyContactResponse])
def read_emergency_contacts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    is_active: Optional[bool] = Query(None),
    is_primary: Optional[bool] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Retrieve emergency contacts for the current user or accessible patient."""

    # Start with base query
    query = db.query(EmergencyContact).filter(
        EmergencyContact.patient_id == target_patient_id
    )

    # Apply optional filters
    if is_active is not None:
        query = query.filter(EmergencyContact.is_active == is_active)

    if is_primary is not None:
        query = query.filter(EmergencyContact.is_primary == is_primary)

    # Order by primary first, then by name
    query = query.order_by(EmergencyContact.is_primary.desc(), EmergencyContact.name)

    # Apply pagination
    contacts = query.offset(skip).limit(limit).all()

    return contacts

# Override the standard get endpoint to use custom query with joinedload
@router.get("/{emergency_contact_id}", response_model=EmergencyContactWithRelations)
def read_emergency_contact(
    emergency_contact_id: int,
    db: Session = Depends(deps.get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
) -> Any:
    """Get emergency contact by ID with related information - only allows access to user's own contacts."""
    # Use direct query with joinedload for relations
    from sqlalchemy.orm import joinedload

    contact_obj = (
        db.query(EmergencyContact)
        .options(joinedload(EmergencyContact.patient))
        .filter(EmergencyContact.id == emergency_contact_id)
        .first()
    )
    handle_not_found(contact_obj, "Emergency Contact")
    verify_patient_ownership(contact_obj, current_user_patient_id, "emergency contact")
    return contact_obj


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
