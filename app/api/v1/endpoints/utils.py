from pathlib import Path
from typing import Any, Optional, Type, List
import traceback

from fastapi import APIRouter, HTTPException, Request, status, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError

from app.api import deps
from app.api.activity_logging import log_create, log_delete, log_update
from app.core.datetime_utils import get_timezone_info
from app.core.logging_config import get_logger
from app.crud.base import CRUDBase
from app.models.activity_log import EntityType

logger = get_logger(__name__, "app")

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/timezone-info")
def timezone_info():
    """Get facility timezone information."""
    return get_timezone_info()


def handle_not_found(obj: Any, entity_name: str) -> None:
    """
    Standard 404 error handler for entities.

    Args:
        obj: The database object (None if not found)
        entity_name: Name of the entity type (e.g., "Medication", "Condition")

    Raises:
        HTTPException: 404 error if object is None
    """
    if not obj:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")


def create_success_response(entity_name: str) -> dict[str, str]:
    """
    Standard success response for delete operations.

    Args:
        entity_name: Name of the entity type (e.g., "Medication", "Condition")

    Returns:
        Dict with success message
    """
    return {"message": f"{entity_name} deleted successfully"}


def verify_patient_ownership(
    obj: Any, current_user_patient_id: int, entity_name: str
) -> None:
    """
    Verify that a medical record belongs to the current user.

    Args:
        obj: The database object to check
        current_user_patient_id: Current user's patient ID
        entity_name: Name of the entity type for error messages

    Raises:
        HTTPException: 404 if object doesn't belong to user
    """
    patient_id = getattr(obj, "patient_id", None)
    deps.verify_patient_record_access(
        patient_id, current_user_patient_id, entity_name.lower()
    )


def handle_entity_operation_logging(
    operation: str,
    entity_name: str,
    entity_id: Optional[int],
    patient_id: Optional[int],
    user_id: int,
    user_ip: str,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """
    Centralized logging for entity operations.

    Args:
        operation: Type of operation (created, updated, deleted)
        entity_name: Name of entity type
        entity_id: ID of the entity
        patient_id: ID of the patient
        user_id: ID of the user performing operation
        user_ip: IP address of the user
        success: Whether operation was successful
        error: Error message if operation failed
    """
    entity_lower = entity_name.lower()
    event_type = f"{entity_lower}_{operation}"

    if not success:
        event_type += "_failed"

    extra_data = {
        "category": "app",
        "event": event_type,
        "user_id": user_id,
        "patient_id": patient_id,
        f"{entity_lower}_id": entity_id,
        "ip": user_ip,
    }

    if error:
        extra_data["error"] = error

    message = f"{entity_name} {operation} {'successfully' if success else 'failed'}"
    if entity_id:
        message += f": {entity_id}"
    if error:
        message += f" - {error}"

    if success:
        logger.info(message, extra=extra_data)
    else:
        logger.error(message, extra=extra_data)


def handle_create_with_logging(
    db: Session,
    crud_obj: Any,
    obj_in: Any,
    entity_type: Any,
    user_id: int,
    entity_name: str,
    request: Optional[Request] = None,
) -> Any:
    """
    Handle entity creation with standardized logging.

    Args:
        db: Database session
        crud_obj: CRUD object for the entity
        obj_in: Input data for creation
        entity_type: EntityType enum value
        user_id: Current user ID
        entity_name: Name of entity type for logging
        request: Request object for additional logging

    Returns:
        Created entity object

    Raises:
        HTTPException: If creation fails
    """
    user_ip = request.client.host if request and request.client else "unknown"

    try:
        entity_obj = crud_obj.create(db=db, obj_in=obj_in)
        entity_id = getattr(entity_obj, "id", None)
        patient_id = getattr(entity_obj, "patient_id", None)

        # Log successful creation
        handle_entity_operation_logging(
            operation="created",
            entity_name=entity_name,
            entity_id=entity_id,
            patient_id=patient_id,
            user_id=user_id,
            user_ip=user_ip,
            success=True,
        )

        # Log activity using centralized logging
        log_create(
            db=db,
            entity_type=entity_type,
            entity_obj=entity_obj,
            user_id=user_id,
            request=request,
        )

        return entity_obj

    except Exception as e:
        # Log failed creation
        patient_id_input = getattr(obj_in, "patient_id", None)
        handle_entity_operation_logging(
            operation="created",
            entity_name=entity_name,
            entity_id=None,
            patient_id=patient_id_input,
            user_id=user_id,
            user_ip=user_ip,
            success=False,
            error=str(e),
        )
        raise


def handle_update_with_logging(
    db: Session,
    crud_obj: Any,
    entity_id: int,
    obj_in: Any,
    entity_type: Any,
    user_id: int,
    entity_name: str,
    request: Optional[Request] = None,
) -> Any:
    """
    Handle entity update with standardized logging.

    Args:
        db: Database session
        crud_obj: CRUD object for the entity
        entity_id: ID of entity to update
        obj_in: Update data
        entity_type: EntityType enum value
        user_id: Current user ID
        entity_name: Name of entity type for logging
        request: Request object for additional logging

    Returns:
        Updated entity object

    Raises:
        HTTPException: If entity not found or update fails
    """
    user_ip = request.client.host if request and request.client else "unknown"

    # Get existing entity
    entity_obj = crud_obj.get(db=db, id=entity_id)
    handle_not_found(entity_obj, entity_name)

    patient_id = getattr(entity_obj, "patient_id", None)

    try:
        updated_entity = crud_obj.update(db=db, db_obj=entity_obj, obj_in=obj_in)

        # Log successful update
        handle_entity_operation_logging(
            operation="updated",
            entity_name=entity_name,
            entity_id=entity_id,
            patient_id=patient_id,
            user_id=user_id,
            user_ip=user_ip,
            success=True,
        )

        # Log activity using centralized logging
        log_update(
            db=db,
            entity_type=entity_type,
            entity_obj=updated_entity,
            user_id=user_id,
            request=request,
        )

        return updated_entity

    except Exception as e:
        # Log failed update
        handle_entity_operation_logging(
            operation="updated",
            entity_name=entity_name,
            entity_id=entity_id,
            patient_id=patient_id,
            user_id=user_id,
            user_ip=user_ip,
            success=False,
            error=str(e),
        )
        raise


def handle_delete_with_logging(
    db: Session,
    crud_obj: Any,
    entity_id: int,
    entity_type: Any,
    user_id: int,
    entity_name: str,
    request: Optional[Request] = None,
) -> dict[str, str]:
    """
    Handle entity deletion with standardized logging.

    Args:
        db: Database session
        crud_obj: CRUD object for the entity
        entity_id: ID of entity to delete
        entity_type: EntityType enum value
        user_id: Current user ID
        entity_name: Name of entity type for logging
        request: Request object for additional logging

    Returns:
        Success response dict

    Raises:
        HTTPException: If entity not found or deletion fails
    """
    user_ip = request.client.host if request and request.client else "unknown"

    # Get existing entity
    entity_obj = crud_obj.get(db=db, id=entity_id)
    handle_not_found(entity_obj, entity_name)

    patient_id = getattr(entity_obj, "patient_id", None)

    try:
        # Log activity BEFORE deleting
        log_delete(
            db=db,
            entity_type=entity_type,
            entity_obj=entity_obj,
            user_id=user_id,
            request=request,
        )

        crud_obj.delete(db=db, id=entity_id)

        # Log successful deletion
        handle_entity_operation_logging(
            operation="deleted",
            entity_name=entity_name,
            entity_id=entity_id,
            patient_id=patient_id,
            user_id=user_id,
            user_ip=user_ip,
            success=True,
        )

        return create_success_response(entity_name)

    except Exception as e:
        # Log failed deletion
        handle_entity_operation_logging(
            operation="deleted",
            entity_name=entity_name,
            entity_id=entity_id,
            patient_id=patient_id,
            user_id=user_id,
            user_ip=user_ip,
            success=False,
            error=str(e),
        )
        raise


def ensure_directory_with_permissions(directory: Path, directory_name: str = "directory") -> None:
    """
    Ensure directory exists with proper error handling for Docker bind mount permission issues.
    
    Args:
        directory: Path object for the directory to create
        directory_name: Human-readable name for error messages
        
    Raises:
        HTTPException: If directory cannot be created due to permissions or other errors
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured {directory_name} directory exists: {directory}")
    except PermissionError as e:
        error_msg = (
            f"Permission denied creating {directory_name} directory: {directory}. "
            "This may be a Docker bind mount permission issue. "
            "Please ensure the container has write permissions to the directory. "
            "Solutions: "
            "1. Use Docker volumes instead of bind mounts, "
            "2. Fix host directory permissions: 'sudo chown -R 1000:1000 /host/path', "
            "3. Add user mapping to docker run: '--user $(id -u):$(id -g)'. "
            f"Error: {str(e)}"
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )
    except OSError as e:
        error_msg = f"Failed to create {directory_name} directory {directory}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


def sanitize_error_for_client(error: Exception, operation_context: str = "operation") -> str:
    """
    Sanitize error messages for client responses to prevent information disclosure.
    
    This function strips internal details like stack traces, database schema information,
    file paths, and other sensitive system details from error messages.
    
    Args:
        error: The exception that occurred
        operation_context: Brief description of the operation that failed (for logging)
        
    Returns:
        A safe, generic error message suitable for client responses
    """
    # Map specific exception types to safe, generic error messages
    error_type = type(error).__name__
    
    # Database-related errors - never expose schema details
    if isinstance(error, (SQLAlchemyError, IntegrityError, DatabaseError)):
        return "A database error occurred. Please try again later."
    
    # Permission/authentication errors - keep generic
    if "permission" in str(error).lower() or "access" in str(error).lower():
        return "Access denied."
    
    # Authentication-related errors - don't reveal specifics
    if any(keyword in str(error).lower() for keyword in ["auth", "token", "login", "credential"]):
        return "Authentication failed."
    
    # Connection/network errors - keep minimal
    if any(keyword in str(error).lower() for keyword in ["connection", "network", "timeout", "refused"]):
        return "Service temporarily unavailable. Please try again later."
    
    # Validation errors - can be more specific but still safe
    if "validation" in str(error).lower() or "invalid" in str(error).lower():
        return "Invalid input provided."
    
    # File/IO errors - don't expose paths
    if isinstance(error, (IOError, OSError, FileNotFoundError, PermissionError)):
        return "File operation failed."
    
    # Default safe message for any other errors
    return f"An error occurred during {operation_context}. Please try again later."


def log_and_sanitize_error(
    logger_instance: Any,
    error: Exception, 
    operation_context: str,
    user_id: Optional[int] = None,
    extra_context: Optional[dict] = None
) -> str:
    """
    Log the full error details server-side and return a sanitized message for the client.
    
    This function ensures that:
    1. Full error details (including stack traces) are logged server-side for debugging
    2. Only safe, sanitized error messages are returned to clients
    3. No internal system details are exposed to clients
    
    Args:
        logger_instance: Logger to use for server-side error logging
        error: The exception that occurred
        operation_context: Brief description of what operation failed
        user_id: ID of the user (if available) for correlation
        extra_context: Additional context data for logging
        
    Returns:
        Sanitized error message safe for client responses
    """
    # Prepare extra logging context
    log_context = {
        "error_type": type(error).__name__,
        "operation": operation_context,
    }
    
    if user_id:
        log_context["user_id"] = user_id
        
    if extra_context:
        log_context.update(extra_context)
    
    # Log full error details server-side (including stack trace for debugging)
    logger_instance.error(
        f"Error during {operation_context}: {str(error)}",
        extra=log_context,
        exc_info=True  # This includes the full stack trace in server logs
    )
    
    # Return sanitized message for client
    return sanitize_error_for_client(error, operation_context)


def create_sanitized_http_exception(
    error: Exception,
    operation_context: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    logger_instance: Optional[Any] = None,
    user_id: Optional[int] = None,
    extra_context: Optional[dict] = None
) -> HTTPException:
    """
    Create an HTTPException with a sanitized error message that doesn't expose internal details.
    
    This function handles the complete flow of:
    1. Logging the full error details server-side
    2. Creating a safe HTTPException for the client
    3. Ensuring no sensitive information is leaked
    
    Args:
        error: The original exception
        operation_context: Description of the operation that failed
        status_code: HTTP status code to return
        logger_instance: Logger for server-side logging (uses default if None)
        user_id: User ID for correlation (if available)
        extra_context: Additional context for logging
        
    Returns:
        HTTPException with sanitized error message
    """
    # Use provided logger or fall back to module logger
    log_instance = logger_instance or logger
    
    # Log error and get sanitized message
    sanitized_message = log_and_sanitize_error(
        log_instance, 
        error, 
        operation_context, 
        user_id, 
        extra_context
    )
    
    return HTTPException(
        status_code=status_code,
        detail=sanitized_message
    )


def add_standard_endpoints(
    router: APIRouter,
    *,
    crud_obj: CRUDBase,
    entity_type: EntityType,
    entity_name: str,
    create_schema: Type,
    update_schema: Type,
    response_schema: Type,
    response_with_relations_schema: Optional[Type] = None
) -> None:
    """
    Add standard CRUD endpoints to an existing router.
    
    This preserves all existing custom endpoints while adding the standard ones:
    - POST /     - Create entity
    - GET /      - List entities 
    - GET /{id}  - Get entity by ID
    - PUT /{id}  - Update entity
    - DELETE /{id} - Delete entity
    
    Args:
        router: FastAPI router to add endpoints to
        crud_obj: CRUD object for the entity
        entity_type: EntityType enum value for logging
        entity_name: Name of entity type for logging and messages
        create_schema: Pydantic schema for creation
        update_schema: Pydantic schema for updates
        response_schema: Pydantic schema for responses
        response_with_relations_schema: Optional schema for responses with relations
    """
    relations_schema = response_with_relations_schema or response_schema
    
    @router.post("/", response_model=response_schema)
    def create_entity(
        *,
        request: Request,
        db: Session = Depends(deps.get_db),
        obj_in: create_schema,
        current_user_id: int = Depends(deps.get_current_user_id),
    ) -> Any:
        """Create new entity record."""
        return handle_create_with_logging(
            db=db, crud_obj=crud_obj, obj_in=obj_in,
            entity_type=entity_type, user_id=current_user_id,
            entity_name=entity_name, request=request
        )
    
    @router.get("/", response_model=List[response_schema])
    def list_entities(
        db: Session = Depends(deps.get_db),
        skip: int = 0,
        limit: int = Query(default=100, le=100),
        target_patient_id: int = Depends(deps.get_accessible_patient_id),
    ) -> Any:
        """Retrieve entities for the current user or accessible patient."""
        return crud_obj.get_by_patient(
            db, patient_id=target_patient_id, skip=skip, limit=limit
        )
    
    @router.get("/{entity_id}", response_model=relations_schema)
    def get_entity(
        *,
        db: Session = Depends(deps.get_db),
        entity_id: int,
        current_user_patient_id: int = Depends(deps.get_current_user_patient_id),
    ) -> Any:
        """Get entity by ID with related information."""
        obj = crud_obj.get_with_relations(
            db=db, record_id=entity_id, relations=["patient"]
        )
        handle_not_found(obj, entity_name)
        verify_patient_ownership(obj, current_user_patient_id, entity_name.lower())
        return obj
    
    @router.put("/{entity_id}", response_model=response_schema)
    def update_entity(
        *,
        request: Request,
        db: Session = Depends(deps.get_db),
        entity_id: int,
        obj_in: update_schema,
        current_user_id: int = Depends(deps.get_current_user_id),
    ) -> Any:
        """Update an entity record."""
        return handle_update_with_logging(
            db=db, crud_obj=crud_obj, entity_id=entity_id, obj_in=obj_in,
            entity_type=entity_type, user_id=current_user_id,
            entity_name=entity_name, request=request
        )
    
    @router.delete("/{entity_id}")
    def delete_entity(
        *,
        request: Request,
        db: Session = Depends(deps.get_db),
        entity_id: int,
        current_user_id: int = Depends(deps.get_current_user_id),
    ) -> Any:
        """Delete an entity record."""
        return handle_delete_with_logging(
            db=db, crud_obj=crud_obj, entity_id=entity_id,
            entity_type=entity_type, user_id=current_user_id,
            entity_name=entity_name, request=request
        )