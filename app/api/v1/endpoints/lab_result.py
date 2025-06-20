from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session
from datetime import datetime
import os
import uuid
from pathlib import Path

from app.api import deps
from app.core.database import get_db
from app.crud.lab_result import lab_result
from app.crud.lab_result_file import lab_result_file
from app.schemas.lab_result import (
    LabResultCreate,
    LabResultUpdate,
    LabResultResponse,
    LabResultWithRelations,
)
from app.schemas.lab_result_file import LabResultFileCreate, LabResultFileResponse
from app.models.activity_log import ActivityLog
from app.models.models import get_utc_now

router = APIRouter()


# Lab Result Endpoints
@router.get("/", response_model=List[LabResultResponse])
def get_lab_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),    db: Session = Depends(get_db),
    current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
):
    """
    Get lab results for the current user with pagination
    """
    # Filter lab results by the user's patient_id
    results = lab_result.get_by_patient(db, patient_id=current_user_patient_id, skip=skip, limit=limit)
    return results


@router.get("/{lab_result_id}", response_model=LabResultWithRelations)
def get_lab_result(
    lab_result_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """
    Get a specific lab result by ID with related data
    """
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    return db_lab_result


@router.post("/", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
def create_lab_result(
    lab_result_in: LabResultCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """
    Create a new lab result
    """
    try:
        db_lab_result = lab_result.create(db, obj_in=lab_result_in)
        
        # Log the creation activity
        try:
            description = f"New lab result: {getattr(db_lab_result, 'test_name', 'Unknown test')}"
            activity_log = ActivityLog(
                user_id=current_user_id,
                patient_id=getattr(db_lab_result, 'patient_id', None),
                action="created",
                entity_type="lab_result",
                entity_id=getattr(db_lab_result, 'id', 0),
                description=description,
                timestamp=get_utc_now(),
            )
            db.add(activity_log)
            db.commit()
        except Exception as e:
            # Don't fail the main operation if logging fails
            db.rollback()
            print(f"Error logging lab result creation activity: {e}")
        
        return db_lab_result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error creating lab result: {str(e)}"
        )


@router.put("/{lab_result_id}", response_model=LabResultResponse)
def update_lab_result(
    lab_result_id: int,
    lab_result_in: LabResultUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    ):    
    """
    Update an existing lab result
    """
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    try:
        updated_lab_result = lab_result.update(
            db, db_obj=db_lab_result, obj_in=lab_result_in
        )
        
        # Log the update activity
        try:
            description = f"Updated lab result: {getattr(updated_lab_result, 'test_name', 'Unknown test')}"
            activity_log = ActivityLog(
                user_id=current_user_id,
                patient_id=getattr(updated_lab_result, 'patient_id', None),
                action="updated",
                entity_type="lab_result",
                entity_id=getattr(updated_lab_result, 'id', 0),
                description=description,
                timestamp=get_utc_now(),
            )
            db.add(activity_log)
            db.commit()
        except Exception as e:
            # Don't fail the main operation if logging fails
            db.rollback()
            print(f"Error logging lab result update activity: {e}")
        
        return updated_lab_result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error updating lab result: {str(e)}"
        )


@router.delete("/{lab_result_id}")
def delete_lab_result(
    lab_result_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
    ):    
    """
    Delete a lab result and associated files
    """
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    try:
        # Log the deletion activity BEFORE deleting
        try:
            description = f"Deleted lab result: {getattr(db_lab_result, 'test_name', 'Unknown test')}"
            activity_log = ActivityLog(
                user_id=current_user_id,
                patient_id=getattr(db_lab_result, 'patient_id', None),
                action="deleted",
                entity_type="lab_result",
                entity_id=getattr(db_lab_result, 'id', 0),
                description=description,
                timestamp=get_utc_now(),
            )
            db.add(activity_log)
            db.commit()
        except Exception as e:
            # Don't fail the main operation if logging fails
            db.rollback()
            print(f"Error logging lab result deletion activity: {e}")

        # Delete associated files first
        lab_result_file.delete_by_lab_result(db, lab_result_id=lab_result_id)

        # Delete the lab result
        lab_result.delete(db, id=lab_result_id)
        return {"message": "Lab result and associated files deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error deleting lab result: {str(e)}"
        )


# Patient-specific endpoints
@router.get("/patient/{patient_id}", response_model=List[LabResultResponse])
def get_lab_results_by_patient(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """
    Get all lab results for a specific patient
    """
    results = lab_result.get_by_patient(
        db, patient_id=patient_id, skip=skip, limit=limit
    )
    return results


@router.get("/patient/{patient_id}/code/{code}", response_model=List[LabResultResponse])
def get_lab_results_by_patient_and_code(
    patient_id: int, code: str, db: Session = Depends(get_db)
):
    """
    Get lab results for a specific patient and test code
    """
    # Get all results for the patient first, then filter by code
    patient_results = lab_result.get_by_patient(db, patient_id=patient_id)
    results = [result for result in patient_results if result.code == code]
    return results


# Practitioner-specific endpoints
@router.get("/practitioner/{practitioner_id}", response_model=List[LabResultResponse])
def get_lab_results_by_practitioner(
    practitioner_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get all lab results ordered by a specific practitioner
    """
    results = lab_result.get_by_practitioner(
        db, practitioner_id=practitioner_id, skip=skip, limit=limit
    )
    return results


# Search endpoints
@router.get("/search/code/{code}", response_model=List[LabResultResponse])
def search_lab_results_by_code(
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Search lab results by test code
    """
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
    code_pattern: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Search lab results by code pattern (partial match)
    """
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
def get_lab_result_files(lab_result_id: int, db: Session = Depends(get_db)):
    """
    Get all files for a specific lab result
    """
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    files = lab_result_file.get_by_lab_result(db, lab_result_id=lab_result_id)
    return files


@router.post("/{lab_result_id}/files", response_model=LabResultFileResponse)
async def upload_lab_result_file(
    lab_result_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(deps.get_current_user_id),
):
    """
    Upload a new file for a lab result
    """
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    # Configuration
    UPLOAD_DIRECTORY = "uploads/lab_result_files"
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

    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}",
        )  # Create file entry in database
    file_create = LabResultFileCreate(
        lab_result_id=lab_result_id,
        file_name=file.filename,
        file_path=file_path,
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
    lab_result_id: int, file_id: int, db: Session = Depends(get_db)
):
    """
    Delete a specific file from a lab result
    """
    # Verify lab result exists
    db_lab_result = lab_result.get(db, id=lab_result_id)
    if not db_lab_result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    # Verify file exists and belongs to this lab result
    db_file = lab_result_file.get(db, id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

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
def get_patient_lab_result_count(patient_id: int, db: Session = Depends(get_db)):
    """
    Get count of lab results for a patient
    """
    results = lab_result.get_by_patient(db, patient_id=patient_id)
    return {"patient_id": patient_id, "lab_result_count": len(results)}


@router.get("/stats/practitioner/{practitioner_id}/count")
def get_practitioner_lab_result_count(
    practitioner_id: int, db: Session = Depends(get_db)
):
    """
    Get count of lab results ordered by a practitioner
    """
    results = lab_result.get_by_practitioner(db, practitioner_id=practitioner_id)
    return {"practitioner_id": practitioner_id, "lab_result_count": len(results)}


@router.get("/stats/code/{code}/count")
def get_code_usage_count(code: str, db: Session = Depends(get_db)):
    """
    Get count of how many times a specific test code has been used
    """
    all_results = lab_result.get_multi(db, skip=0, limit=10000)
    results = [result for result in all_results if result.code == code]
    return {"code": code, "usage_count": len(results)}
