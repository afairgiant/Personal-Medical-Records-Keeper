import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.utils import (
    ensure_directory_with_permissions,
    handle_create_with_logging,
    handle_delete_with_logging,
    handle_not_found,
    handle_update_with_logging,
    add_standard_endpoints,
)
from app.core.config import settings
from app.core.database import get_db
from app.crud.condition import condition as condition_crud
from app.crud.lab_result import lab_result, lab_result_condition
from app.crud.lab_result_file import lab_result_file
from app.models.activity_log import EntityType
from app.models.models import EntityFile, User
from app.services.generic_entity_file_service import GenericEntityFileService
from app.schemas.lab_result import (
    LabResultConditionCreate,
    LabResultConditionResponse,
    LabResultConditionUpdate,
    LabResultConditionWithDetails,
    LabResultCreate,
    LabResultResponse,
    LabResultUpdate,
    LabResultWithRelations,
)
from app.schemas.lab_result_file import LabResultFileCreate, LabResultFileResponse

router = APIRouter()

# Add standard CRUD endpoints with custom delete override
add_standard_endpoints(
    router,
    crud_obj=lab_result,
    entity_type=EntityType.LAB_RESULT,
    entity_name="Lab result",
    create_schema=LabResultCreate,
    update_schema=LabResultUpdate,
    response_schema=LabResultResponse,
    response_with_relations_schema=LabResultWithRelations,
)

# Override the standard list endpoint with custom response formatting
@router.get("/", response_model=List[LabResultWithRelations])
def get_lab_results(
    *,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db),
    target_patient_id: int = Depends(deps.get_accessible_patient_id),
):
    """Get lab results for the current user or accessible patient."""

    # Filter lab results by the target patient_id with practitioner relationship loaded
    results = lab_result.get_by_patient(
        db,
        patient_id=target_patient_id,
        skip=skip,
        limit=limit,
        load_relations=["practitioner", "patient"],
    )

    # Convert to response format with practitioner names
    response_results = []
    for result in results:
        result_dict = {
            "id": result.id,
            "patient_id": result.patient_id,
            "practitioner_id": result.practitioner_id,
            "test_name": result.test_name,
            "test_code": result.test_code,
            "test_category": result.test_category,
            "test_type": result.test_type,
            "facility": result.facility,
            "status": result.status,
            "labs_result": result.labs_result,
            "ordered_date": result.ordered_date,
            "completed_date": result.completed_date,
            "notes": result.notes,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "practitioner_name": (
                result.practitioner.name if result.practitioner else None
            ),
            "patient_name": (
                f"{result.patient.first_name} {result.patient.last_name}"
                if result.patient
                else None
            ),
            "files": [],  # Files will be loaded separately if needed
        }
        response_results.append(result_dict)

    return response_results

# Override the standard get endpoint with custom response formatting
@router.get("/{lab_result_id}", response_model=LabResultWithRelations)
def get_lab_result(
    *,
    lab_result_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """Get a specific lab result by ID with related data."""
    db_lab_result = lab_result.get_with_relations(
        db=db, record_id=lab_result_id, relations=["patient", "practitioner"]
    )
    handle_not_found(db_lab_result, "Lab result")
    assert (
        db_lab_result is not None
    )  # Type checker hint - handle_not_found raises if None

    # Convert to response format with practitioner name
    result_dict = {
        "id": db_lab_result.id,
        "patient_id": db_lab_result.patient_id,
        "practitioner_id": db_lab_result.practitioner_id,
        "test_name": db_lab_result.test_name,
        "test_code": db_lab_result.test_code,
        "test_category": db_lab_result.test_category,
        "test_type": db_lab_result.test_type,
        "facility": db_lab_result.facility,
        "status": db_lab_result.status,
        "labs_result": db_lab_result.labs_result,
        "ordered_date": db_lab_result.ordered_date,
        "completed_date": db_lab_result.completed_date,
        "notes": db_lab_result.notes,
        "created_at": db_lab_result.created_at,
        "updated_at": db_lab_result.updated_at,
        "practitioner_name": (
            db_lab_result.practitioner.name if db_lab_result.practitioner else None
        ),
        "patient_name": (
            f"{db_lab_result.patient.first_name} {db_lab_result.patient.last_name}"
            if db_lab_result.patient
            else None
        ),
        "files": db_lab_result.files or [],
    }

    return result_dict

# Override the standard delete endpoint with custom file handling logic
@router.delete("/{lab_result_id}")
def delete_lab_result(
    *,
    lab_result_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """Delete a lab result and associated files."""
    # Custom deletion logic to handle associated files
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    try:
        # Log the deletion activity BEFORE deleting
        from app.api.activity_logging import log_delete
        from app.core.logging_config import get_logger
        
        logger = get_logger(__name__)

        log_delete(
            db=db,
            entity_type=EntityType.LAB_RESULT,
            entity_obj=db_lab_result,
            user_id=current_user_id,
            request=request,
        )

        # Delete associated files from both old and new systems
        # 1. Delete old system files (LabResultFile table)
        lab_result_file.delete_by_lab_result(db, lab_result_id=lab_result_id)
        
        # 2. Delete new system files (EntityFile table) with selective deletion
        entity_file_service = GenericEntityFileService()
        file_cleanup_stats = entity_file_service.cleanup_entity_files_on_deletion(
            db=db,
            entity_type="lab-result",
            entity_id=lab_result_id,
            preserve_paperless=True
        )
        
        deleted_local_files = file_cleanup_stats.get("files_deleted", 0)
        preserved_paperless_files = file_cleanup_stats.get("files_preserved", 0)
        
        logger.info(f"EntityFile cleanup completed: {deleted_local_files} local files deleted, {preserved_paperless_files} Paperless files preserved")

        # Delete the lab result
        lab_result.delete(db, id=lab_result_id)
        
        return {
            "message": "Lab result and associated files deleted successfully",
            "files_deleted": deleted_local_files,
            "files_preserved": preserved_paperless_files
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error deleting lab result: {str(e)}"
        )


# Patient-specific endpoints
@router.get("/patient/{patient_id}", response_model=List[LabResultResponse])
def get_lab_results_by_patient(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    patient_id: int = Depends(deps.verify_patient_access),
):
    """Get all lab results for a specific patient."""
    results = lab_result.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return results


@router.get("/patient/{patient_id}/code/{code}", response_model=List[LabResultResponse])
def get_lab_results_by_patient_and_code(
    *,
    code: str,
    db: Session = Depends(get_db),
    patient_id: int = Depends(deps.verify_patient_access),
):
    """Get lab results for a specific patient and test code."""
    # Get all results for the patient first, then filter by code
    patient_results = lab_result.get_by_patient(db, patient_id=patient_id)
    results = [result for result in patient_results if result.code == code]
    return results


# Practitioner-specific endpoints
@router.get("/practitioner/{practitioner_id}", response_model=List[LabResultResponse])
def get_lab_results_by_practitioner(
    *,
    practitioner_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all lab results ordered by a specific practitioner."""
    results = lab_result.get_by_practitioner(
        db, practitioner_id=practitioner_id, skip=skip, limit=limit
    )
    return results


# Search endpoints
@router.get("/search/code/{code}", response_model=List[LabResultResponse])
def search_lab_results_by_code(
    *,
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Search lab results by test code."""
    # Get all results and filter by code - replace with proper CRUD method if available
    all_results = lab_result.get_multi(db, skip=0, limit=10000)
    filtered_results = [result for result in all_results if result.code == code]
    # Apply pagination
    paginated_results = (
        filtered_results[skip : skip + limit] if limit else filtered_results[skip:]
    )
    return paginated_results


@router.get(
    "/search/code-pattern/{code_pattern}", response_model=List[LabResultResponse]
)
def search_lab_results_by_code_pattern(
    *,
    code_pattern: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Search lab results by code pattern (partial match)."""
    # Get all results and filter by code pattern - replace with proper CRUD method if available
    all_results = lab_result.get_multi(db, skip=0, limit=10000)
    filtered_results = [
        result for result in all_results if code_pattern.lower() in result.code.lower()
    ]
    # Apply pagination
    paginated_results = (
        filtered_results[skip : skip + limit] if limit else filtered_results[skip:]
    )
    return paginated_results


# File Management Endpoints
@router.get("/{lab_result_id}/files", response_model=List[LabResultFileResponse])
def get_lab_result_files(*, lab_result_id: int, db: Session = Depends(get_db)):
    """Get all files for a specific lab result."""
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    files = lab_result_file.get_by_lab_result(db, lab_result_id=lab_result_id)
    return files


@router.post("/{lab_result_id}/files", response_model=LabResultFileResponse)
async def upload_lab_result_file(
    *,
    lab_result_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """Upload a new file for a lab result."""
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    # Configuration
    UPLOAD_DIRECTORY = settings.UPLOAD_DIR / "lab_result_files"
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".bmp",
        ".gif",
        ".txt",
        ".csv",
        ".xml",
        ".json",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".dcm",
    }

    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Create upload directory if it doesn't exist with proper error handling
    ensure_directory_with_permissions(UPLOAD_DIRECTORY, "lab result file upload")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIRECTORY / unique_filename

    # Save file with proper error handling
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Permission denied writing file. This may be a Docker bind mount permission issue. Please ensure the container has write permissions to the upload directory: {str(e)}",
        )
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}",
        )

    # Create file entry in database
    file_create = LabResultFileCreate(
        lab_result_id=lab_result_id,
        file_name=file.filename,
        file_path=str(file_path),
        file_type=file.content_type,
        file_size=len(file_content),
        description=description,
        uploaded_at=datetime.utcnow(),
    )

    try:
        db_file = lab_result_file.create(db, obj_in=file_create)
        return db_file
    except Exception as e:
        # Clean up the uploaded file if database operation fails
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=400, detail=f"Error creating file record: {str(e)}"
        )


@router.delete("/{lab_result_id}/files/{file_id}")
def delete_lab_result_file(
    *, lab_result_id: int, file_id: int, db: Session = Depends(get_db)
):
    """Delete a specific file from a lab result."""
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    # Verify file exists and belongs to this lab result
    db_file = lab_result_file.get(db, id=file_id)
    handle_not_found(db_file, "File")

    if getattr(db_file, "lab_result_id") != lab_result_id:
        raise HTTPException(
            status_code=400, detail="File does not belong to this lab result"
        )

    try:
        lab_result_file.delete(db, id=file_id)
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting file: {str(e)}")


# Statistics endpoints
@router.get("/stats/patient/{patient_id}/count")
def get_patient_lab_result_count(
    *,
    db: Session = Depends(get_db),
    patient_id: int = Depends(deps.verify_patient_access),
):
    """Get count of lab results for a patient."""
    results = lab_result.get_by_patient(db, patient_id=patient_id)
    return {"patient_id": patient_id, "lab_result_count": len(results)}


@router.get("/stats/practitioner/{practitioner_id}/count")
def get_practitioner_lab_result_count(
    *, practitioner_id: int, db: Session = Depends(get_db)
):
    """Get count of lab results ordered by a practitioner."""
    results = lab_result.get_by_practitioner(db, practitioner_id=practitioner_id)
    return {"practitioner_id": practitioner_id, "lab_result_count": len(results)}


@router.get("/stats/code/{code}/count")
def get_code_usage_count(*, code: str, db: Session = Depends(get_db)):
    """Get count of how many times a specific test code has been used."""
    all_results = lab_result.get_multi(db, skip=0, limit=10000)
    results = [result for result in all_results if result.code == code]
    return {"code": code, "usage_count": len(results)}


# Lab Result - Condition Relationship Endpoints


@router.get(
    "/{lab_result_id}/conditions", response_model=List[LabResultConditionWithDetails]
)
def get_lab_result_conditions(
    *,
    lab_result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get all condition relationships for a specific lab result."""
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    # Verify user has access to this lab result's patient
    from app.services.patient_access import PatientAccessService
    from app.models.models import Patient
    
    patient_record = db.query(Patient).filter(Patient.id == db_lab_result.patient_id).first()
    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found for this lab result",
        )
    
    access_service = PatientAccessService(db)
    if not access_service.can_access_patient(current_user, patient_record, "view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this lab result",
        )

    # Get condition relationships
    relationships = lab_result_condition.get_by_lab_result(
        db, lab_result_id=lab_result_id
    )

    # Enhance with condition details
    from app.crud.condition import condition as condition_crud

    enhanced_relationships = []
    for rel in relationships:
        condition_obj = condition_crud.get(db, id=rel.condition_id)
        rel_dict = {
            "id": rel.id,
            "lab_result_id": rel.lab_result_id,
            "condition_id": rel.condition_id,
            "relevance_note": rel.relevance_note,
            "created_at": rel.created_at,
            "updated_at": rel.updated_at,
            "condition": (
                {
                    "id": condition_obj.id,
                    "diagnosis": condition_obj.diagnosis,
                    "status": condition_obj.status,
                    "severity": condition_obj.severity,
                }
                if condition_obj
                else None
            ),
        }
        enhanced_relationships.append(rel_dict)

    return enhanced_relationships


@router.post("/{lab_result_id}/conditions", response_model=LabResultConditionResponse)
def create_lab_result_condition(
    *,
    lab_result_id: int,
    condition_in: LabResultConditionCreate,
    db: Session = Depends(get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
):
    """Create a new lab result condition relationship."""
    # Verify lab result exists and belongs to user
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    if db_lab_result.patient_id != current_user_patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this lab result",
        )

    # Verify condition exists and belongs to the same patient
    db_condition = condition_crud.get(db, id=condition_in.condition_id)
    handle_not_found(db_condition, "Condition")

    # Ensure condition belongs to the same patient as the lab result
    if db_condition.patient_id != current_user_patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot link condition that doesn't belong to the same patient",
        )

    # Check if relationship already exists
    existing = lab_result_condition.get_by_lab_result_and_condition(
        db, lab_result_id=lab_result_id, condition_id=condition_in.condition_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship between this lab result and condition already exists",
        )

    # Override lab_result_id to ensure consistency
    condition_in.lab_result_id = lab_result_id

    # Create relationship
    relationship = lab_result_condition.create(db, obj_in=condition_in)
    return relationship


@router.put(
    "/{lab_result_id}/conditions/{relationship_id}",
    response_model=LabResultConditionResponse,
)
def update_lab_result_condition(
    *,
    lab_result_id: int,
    relationship_id: int,
    condition_in: LabResultConditionUpdate,
    db: Session = Depends(get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
):
    """Update a lab result condition relationship."""
    # Verify lab result exists and belongs to user
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    if db_lab_result.patient_id != current_user_patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this lab result",
        )

    # Verify relationship exists
    relationship = lab_result_condition.get(db, id=relationship_id)
    handle_not_found(relationship, "Lab result condition relationship")

    if relationship.lab_result_id != lab_result_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship does not belong to this lab result",
        )

    # Update relationship
    updated_relationship = lab_result_condition.update(
        db, db_obj=relationship, obj_in=condition_in
    )
    return updated_relationship


@router.delete("/{lab_result_id}/conditions/{relationship_id}")
def delete_lab_result_condition(
    *,
    lab_result_id: int,
    relationship_id: int,
    db: Session = Depends(get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
):
    """Delete a lab result condition relationship."""
    # Verify lab result exists and belongs to user
    db_lab_result = lab_result.get(db, id=lab_result_id)
    handle_not_found(db_lab_result, "Lab result")

    if db_lab_result.patient_id != current_user_patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this lab result",
        )

    # Verify relationship exists
    relationship = lab_result_condition.get(db, id=relationship_id)
    handle_not_found(relationship, "Lab result condition relationship")

    if relationship.lab_result_id != lab_result_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relationship does not belong to this lab result",
        )

    # Delete relationship
    lab_result_condition.delete(db, id=relationship_id)
    return {"message": "Lab result condition relationship deleted successfully"}
