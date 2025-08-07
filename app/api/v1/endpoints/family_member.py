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
from app.crud.family_member import family_member
from app.crud.family_condition import family_condition
from app.models.activity_log import EntityType
from app.schemas.family_member import (
    FamilyMemberCreate,
    FamilyMemberDropdownOption,
    FamilyMemberResponse,
    FamilyMemberSummary,
    FamilyMemberUpdate,
)
from app.schemas.family_condition import (
    FamilyConditionCreate,
    FamilyConditionResponse,
    FamilyConditionUpdate,
)

router = APIRouter()

# Custom endpoints defined BEFORE standard CRUD to avoid path conflicts

# Custom LIST endpoint with relationship filtering
@router.get("/", response_model=List[FamilyMemberResponse])
def read_family_members(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    relationship: Optional[str] = Query(None),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Retrieve family members for the current user or accessible patient."""
    
    if relationship:
        family_members = family_member.get_by_relationship(
            db, patient_id=target_patient_id, relationship=relationship
        )
    else:
        family_members = family_member.get_by_patient_with_conditions(
            db, patient_id=target_patient_id
        )
    return family_members

# Dropdown endpoint (before standard endpoints)
@router.get("/dropdown", response_model=List[FamilyMemberDropdownOption])
def get_family_members_for_dropdown(
    *,
    db: Session = Depends(deps.get_db),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Get family members formatted for dropdown selection in forms."""
    family_members = family_member.get_by_patient(db, patient_id=target_patient_id)
    return family_members


# Search endpoint (before standard endpoints)
@router.get("/search/", response_model=List[FamilyMemberResponse])
def search_family_members(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Query(..., min_length=2),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Search family members by name - supports patient switching."""
    family_members = family_member.search_by_name(
        db, patient_id=target_patient_id, name_term=name
    )
    return family_members


# Add standard CRUD endpoints AFTER custom endpoints to avoid conflicts
# This will create: POST /, GET /{entity_id}, PUT /{entity_id}, DELETE /{entity_id}
# Standard endpoints work with patient switching through deps.get_accessible_patient_id
add_standard_endpoints(
    router,
    crud_obj=family_member,
    entity_type=EntityType.FAMILY_MEMBER,
    entity_name="FamilyMember",
    create_schema=FamilyMemberCreate,
    update_schema=FamilyMemberUpdate,
    response_schema=FamilyMemberResponse,
    response_with_relations_schema=FamilyMemberResponse,  # No separate WithRelations schema
)

# Family Condition Endpoints

@router.get("/{family_member_id}/conditions", response_model=List[FamilyConditionResponse])
def get_family_member_conditions(
    *,
    family_member_id: int,
    db: Session = Depends(deps.get_db),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Get all conditions for a specific family member - supports patient switching."""
    # Verify family member exists and belongs to the accessible patient
    family_member_obj = family_member.get(db, id=family_member_id)
    handle_not_found(family_member_obj, "Family Member")
    verify_patient_ownership(family_member_obj, target_patient_id, "family_member")
    
    # Get conditions
    conditions = family_condition.get_by_family_member(db, family_member_id=family_member_id)
    return conditions


@router.post("/{family_member_id}/conditions", response_model=FamilyConditionResponse)
def create_family_condition(
    *,
    family_member_id: int,
    condition_in: FamilyConditionCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Create a new condition for a family member - supports patient switching."""
    # Verify family member exists and belongs to the accessible patient
    family_member_obj = family_member.get(db, id=family_member_id)
    handle_not_found(family_member_obj, "Family Member")
    verify_patient_ownership(family_member_obj, target_patient_id, "family_member")
    
    # Set family_member_id
    condition_in.family_member_id = family_member_id
    
    return handle_create_with_logging(
        db=db,
        crud_obj=family_condition,
        obj_in=condition_in,
        entity_type=EntityType.FAMILY_CONDITION,
        user_id=current_user_id,
        entity_name="Family Condition",
        request=request,
    )


@router.put("/{family_member_id}/conditions/{condition_id}", response_model=FamilyConditionResponse)
def update_family_condition(
    *,
    family_member_id: int,
    condition_id: int,
    condition_in: FamilyConditionUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Update a family member condition - supports patient switching."""
    # Verify family member exists and belongs to the accessible patient
    family_member_obj = family_member.get(db, id=family_member_id)
    handle_not_found(family_member_obj, "Family Member")
    verify_patient_ownership(family_member_obj, target_patient_id, "family_member")
    
    # Get the condition
    condition_obj = family_condition.get(db, id=condition_id)
    handle_not_found(condition_obj, "Family Condition")
    
    # Verify the condition belongs to the specified family member
    if condition_obj.family_member_id != family_member_id:
        raise HTTPException(
            status_code=400,
            detail="Condition does not belong to the specified family member"
        )
    
    return handle_update_with_logging(
        db=db,
        crud_obj=family_condition,
        entity_id=condition_id,
        obj_in=condition_in,
        entity_type=EntityType.FAMILY_CONDITION,
        user_id=current_user_id,
        entity_name="Family Condition",
        request=request,
    )


@router.delete("/{family_member_id}/conditions/{condition_id}")
def delete_family_condition(
    *,
    family_member_id: int,
    condition_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
) -> Any:
    """Delete a family member condition - supports patient switching."""
    # Verify family member exists and belongs to the accessible patient
    family_member_obj = family_member.get(db, id=family_member_id)
    handle_not_found(family_member_obj, "Family Member")
    verify_patient_ownership(family_member_obj, target_patient_id, "family_member")
    
    # Get the condition
    condition_obj = family_condition.get(db, id=condition_id)
    handle_not_found(condition_obj, "Family Condition")
    
    # Verify the condition belongs to the specified family member
    if condition_obj.family_member_id != family_member_id:
        raise HTTPException(
            status_code=400,
            detail="Condition does not belong to the specified family member"
        )
    
    return handle_delete_with_logging(
        db=db,
        crud_obj=family_condition,
        entity_id=condition_id,
        entity_type=EntityType.FAMILY_CONDITION,
        user_id=current_user_id,
        entity_name="Family Condition",
        request=request,
    )