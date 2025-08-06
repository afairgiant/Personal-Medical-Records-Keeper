from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.models import Base


# Timezone-aware datetime function to replace deprecated datetime.utcnow()
def get_utc_now():
    """Get the current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class ActivityLog(Base):
    """
    Centralized activity logging table for tracking all user actions
    and system events in the medical records system.
    """

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)

    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    # Activity details
    action = Column(
        String, nullable=False
    )  # 'created', 'updated', 'deleted', 'viewed', 'downloaded'
    entity_type = Column(
        String, nullable=False
    )  # 'patient', 'medication', 'lab_result', 'condition', etc.
    entity_id = Column(Integer, nullable=True)  # ID of the affected record

    # Human-readable description
    description = Column(Text, nullable=False)
    # Technical details (JSON for flexibility)
    event_metadata = Column(
        JSON, nullable=True
    )  # Store additional context like IP, changes made, etc.
    # Timestamps
    timestamp = Column(DateTime, default=get_utc_now, nullable=False)

    # Client information
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Database indexes for efficient querying
    __table_args__ = (
        Index("idx_activity_user_timestamp", "user_id", "timestamp"),
        Index("idx_activity_patient_timestamp", "patient_id", "timestamp"),
        Index("idx_activity_entity", "entity_type", "entity_id"),
        Index("idx_activity_timestamp", "timestamp"),
        Index("idx_activity_action", "action"),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity log to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "patient_id": self.patient_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "description": self.description,
            "metadata": self.metadata,
            "timestamp": (
                self.timestamp.isoformat() if self.timestamp is not None else None
            ),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

    @classmethod
    def create_activity(
        cls,
        action: str,
        entity_type: str,
        description: str,
        user_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "ActivityLog":
        """
        Factory method to create a new activity log entry

        Args:
            action: The action performed (use ActionType constants)
            entity_type: Type of entity affected (use EntityType constants)
            description: Human-readable description
            user_id: ID of user who performed the action
            patient_id: ID of patient whose data was affected
            entity_id: ID of the specific record affected
            metadata: Additional context data
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            ActivityLog instance
        """
        return cls(
            action=action,
            entity_type=entity_type,
            description=description,
            user_id=user_id,
            patient_id=patient_id,
            entity_id=entity_id,
            event_metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=get_utc_now(),
        )


class EntityType:
    """Constants for entity types that can be logged"""

    # Core entities
    USER = "user"
    PATIENT = "patient"
    PRACTITIONER = "practitioner"

    # Medical records
    MEDICATION = "medication"
    LAB_RESULT = "lab_result"
    LAB_RESULT_FILE = "lab_result_file"
    ENTITY_FILE = "entity_file"
    CONDITION = "condition"
    TREATMENT = "treatment"
    IMMUNIZATION = "immunization"
    ALLERGY = "allergy"
    PROCEDURE = "procedure"
    ENCOUNTER = "encounter"
    EMERGENCY_CONTACT = "emergency_contact"
    VITALS = "vitals"
    PHARMACY = "pharmacy"
    FAMILY_MEMBER = "family_member"
    INSURANCE = "insurance"
    FAMILY_CONDITION = "family_condition"

    # System entities
    SYSTEM = "system"
    BACKUP = "backup"

    @classmethod
    def get_all_types(cls) -> list:
        """Get all available entity types"""
        return [
            cls.USER,
            cls.PATIENT,
            cls.PRACTITIONER,
            cls.MEDICATION,
            cls.LAB_RESULT,
            cls.LAB_RESULT_FILE,
            cls.ENTITY_FILE,
            cls.CONDITION,
            cls.TREATMENT,
            cls.IMMUNIZATION,
            cls.ALLERGY,
            cls.PROCEDURE,
            cls.ENCOUNTER,
            cls.EMERGENCY_CONTACT,
            cls.VITALS,
            cls.PHARMACY,
            cls.FAMILY_MEMBER,
            cls.INSURANCE,
            cls.FAMILY_CONDITION,
            cls.SYSTEM,
            cls.BACKUP,
        ]


class ActionType:
    """Constants for action types that can be performed"""

    # CRUD operations
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    VIEWED = "viewed"

    # File operations
    UPLOADED = "uploaded"
    DOWNLOADED = "downloaded"

    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"

    # Status changes
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    # System events
    BACKUP_CREATED = "backup_created"
    MAINTENANCE_STARTED = "maintenance_started"
    MAINTENANCE_COMPLETED = "maintenance_completed"

    @classmethod
    def get_all_actions(cls) -> list:
        """Get all available action types"""
        return [
            cls.CREATED,
            cls.UPDATED,
            cls.DELETED,
            cls.VIEWED,
            cls.UPLOADED,
            cls.DOWNLOADED,
            cls.LOGIN,
            cls.LOGOUT,
            cls.ACTIVATED,
            cls.DEACTIVATED,
            cls.COMPLETED,
            cls.CANCELLED,
            cls.BACKUP_CREATED,
            cls.MAINTENANCE_STARTED,
            cls.MAINTENANCE_COMPLETED,
        ]


class ActivityCategory:
    """Constants for activity categorization"""

    # Patient management
    PATIENT_CREATED = "patient_created"
    PATIENT_UPDATED = "patient_updated"
    PATIENT_VIEWED = "patient_viewed"
    PATIENT_DELETED = "patient_deleted"

    # Medical records
    MEDICATION_ADDED = "medication_added"
    MEDICATION_UPDATED = "medication_updated"
    MEDICATION_DELETED = "medication_deleted"

    LAB_RESULT_CREATED = "lab_result_created"
    LAB_RESULT_UPDATED = "lab_result_updated"
    LAB_RESULT_VIEWED = "lab_result_viewed"
    LAB_RESULT_DELETED = "lab_result_deleted"
    LAB_FILE_UPLOADED = "lab_file_uploaded"
    LAB_FILE_DOWNLOADED = "lab_file_downloaded"
    LAB_FILE_DELETED = "lab_file_deleted"

    CONDITION_ADDED = "condition_added"
    CONDITION_UPDATED = "condition_updated"
    CONDITION_DELETED = "condition_deleted"

    TREATMENT_STARTED = "treatment_started"
    TREATMENT_UPDATED = "treatment_updated"
    TREATMENT_COMPLETED = "treatment_completed"
    TREATMENT_DELETED = "treatment_deleted"

    IMMUNIZATION_ADDED = "immunization_added"
    IMMUNIZATION_UPDATED = "immunization_updated"
    IMMUNIZATION_DELETED = "immunization_deleted"

    ALLERGY_ADDED = "allergy_added"
    ALLERGY_UPDATED = "allergy_updated"
    ALLERGY_DELETED = "allergy_deleted"

    PROCEDURE_ADDED = "procedure_added"
    PROCEDURE_UPDATED = "procedure_updated"
    PROCEDURE_DELETED = "procedure_deleted"

    ENCOUNTER_ADDED = "encounter_added"
    ENCOUNTER_UPDATED = "encounter_updated"
    ENCOUNTER_DELETED = "encounter_deleted"

    INSURANCE_ADDED = "insurance_added"
    INSURANCE_UPDATED = "insurance_updated"
    INSURANCE_DELETED = "insurance_deleted"
    INSURANCE_SET_PRIMARY = "insurance_set_primary"

    # System events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTERED = "user_registered"
    PASSWORD_CHANGED = "password_changed"

    # Admin events
    ADMIN_ACCESS = "admin_access"
    BACKUP_CREATED = "backup_created"
    SYSTEM_MAINTENANCE = "system_maintenance"
    BULK_OPERATION = "bulk_operation"

    @classmethod
    def get_medical_activities(cls) -> list:
        """Get all medical-related activity categories"""
        return [
            cls.PATIENT_CREATED,
            cls.PATIENT_UPDATED,
            cls.PATIENT_VIEWED,
            cls.PATIENT_DELETED,
            cls.MEDICATION_ADDED,
            cls.MEDICATION_UPDATED,
            cls.MEDICATION_DELETED,
            cls.LAB_RESULT_CREATED,
            cls.LAB_RESULT_UPDATED,
            cls.LAB_RESULT_VIEWED,
            cls.LAB_RESULT_DELETED,
            cls.LAB_FILE_UPLOADED,
            cls.LAB_FILE_DOWNLOADED,
            cls.LAB_FILE_DELETED,
            cls.CONDITION_ADDED,
            cls.CONDITION_UPDATED,
            cls.CONDITION_DELETED,
            cls.TREATMENT_STARTED,
            cls.TREATMENT_UPDATED,
            cls.TREATMENT_COMPLETED,
            cls.TREATMENT_DELETED,
            cls.IMMUNIZATION_ADDED,
            cls.IMMUNIZATION_UPDATED,
            cls.IMMUNIZATION_DELETED,
            cls.ALLERGY_ADDED,
            cls.ALLERGY_UPDATED,
            cls.ALLERGY_DELETED,
            cls.PROCEDURE_ADDED,
            cls.PROCEDURE_UPDATED,
            cls.PROCEDURE_DELETED,
            cls.ENCOUNTER_ADDED,
            cls.ENCOUNTER_UPDATED,
            cls.ENCOUNTER_DELETED,
            cls.INSURANCE_ADDED,
            cls.INSURANCE_UPDATED,
            cls.INSURANCE_DELETED,
            cls.INSURANCE_SET_PRIMARY,
        ]

    @classmethod
    def get_admin_activities(cls) -> list:
        """Get all admin-related activity categories"""
        return [
            cls.ADMIN_ACCESS,
            cls.BACKUP_CREATED,
            cls.SYSTEM_MAINTENANCE,
            cls.BULK_OPERATION,
        ]

    @classmethod
    def get_user_activities(cls) -> list:
        """Get all user-related activity categories"""
        return [
            cls.USER_LOGIN,
            cls.USER_LOGOUT,
            cls.USER_REGISTERED,
            cls.PASSWORD_CHANGED,
        ]


class ActivityPriority:
    """Constants for activity priority levels"""

    LOW = "low"  # Regular viewing, routine updates
    MEDIUM = "medium"  # Creating/updating medical records
    HIGH = "high"  # Deleting records, admin actions
    CRITICAL = "critical"  # Security events, system failures

    @classmethod
    def get_priority_for_action(cls, action: str, entity_type: str) -> str:
        """
        Determine priority level based on action and entity type

        Args:
            action: Action performed
            entity_type: Type of entity affected

        Returns:
            Priority level string
        """
        # Critical priority actions
        if action in [ActionType.DELETED]:
            return cls.CRITICAL

        # High priority actions
        if (
            action in [ActionType.LOGIN, ActionType.LOGOUT]
            and entity_type == EntityType.USER
        ):
            return cls.HIGH

        # Medium priority actions
        if action in [ActionType.CREATED, ActionType.UPDATED]:
            return cls.MEDIUM

        # Default to low priority
        return cls.LOW
