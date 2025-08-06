from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.models import EmergencyContact
from app.schemas.emergency_contact import EmergencyContactCreate, EmergencyContactUpdate


class CRUDEmergencyContact(
    CRUDBase[EmergencyContact, EmergencyContactCreate, EmergencyContactUpdate]
):
    """
    Emergency Contact CRUD operations.

    Manages emergency contacts for patients with proper validation
    and relationship handling.
    """

    def get_by_patient_id(
        self, db: Session, *, patient_id: int
    ) -> List[EmergencyContact]:
        """
        Get all emergency contacts for a specific patient.

        Args:
            db: Database session
            patient_id: ID of the patient

        Returns:
            List of emergency contacts for the patient
        """
        return self.query(
            db=db,
            filters={"patient_id": patient_id},
            order_by="name",
        )

    def get_primary_contact(
        self, db: Session, *, patient_id: int
    ) -> Optional[EmergencyContact]:
        """
        Get the primary emergency contact for a patient.

        Args:
            db: Database session
            patient_id: ID of the patient

        Returns:
            Primary emergency contact if exists, None otherwise
        """
        contacts = self.query(
            db=db,
            filters={"patient_id": patient_id, "is_primary": True, "is_active": True},
            limit=1,
        )
        return contacts[0] if contacts else None

    def set_primary_contact(
        self, db: Session, *, contact_id: int, patient_id: int
    ) -> EmergencyContact:
        """
        Set a contact as the primary emergency contact.
        This will unset any existing primary contact for the patient.

        Args:
            db: Database session
            contact_id: ID of the contact to set as primary
            patient_id: ID of the patient

        Returns:
            Updated emergency contact
        """
        # First, unset any existing primary contact
        existing_primary = self.get_primary_contact(db, patient_id=patient_id)
        if existing_primary and existing_primary.id != contact_id:
            self.update(db, db_obj=existing_primary, obj_in={"is_primary": False})

        # Set the new primary contact
        contact = self.get(db, id=contact_id)
        if contact and contact.patient_id == patient_id:
            return self.update(db, db_obj=contact, obj_in={"is_primary": True})

        raise ValueError("Contact not found or doesn't belong to this patient")

    def create_for_patient(
        self, db: Session, *, patient_id: int, obj_in: EmergencyContactCreate
    ) -> EmergencyContact:
        """
        Create an emergency contact for a patient.

        Args:
            db: Database session
            patient_id: ID of the patient
            obj_in: Emergency contact creation data

        Returns:
            Created emergency contact
        """
        # Set the patient_id
        create_data = obj_in.dict()
        create_data["patient_id"] = patient_id

        # If this is marked as primary, unset any existing primary contact
        if create_data.get("is_primary", False):
            existing_primary = self.get_primary_contact(db, patient_id=patient_id)
            if existing_primary:
                self.update(db, db_obj=existing_primary, obj_in={"is_primary": False})

        # Create the new contact
        db_obj = EmergencyContact(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active_contacts(
        self, db: Session, *, patient_id: int
    ) -> List[EmergencyContact]:
        """
        Get all active emergency contacts for a patient.
        Ordered by primary contact first, then by name.

        Args:
            db: Database session
            patient_id: ID of the patient

        Returns:
            List of active emergency contacts
        """
        from sqlalchemy import desc, asc
        
        return (
            db.query(EmergencyContact)
            .filter(EmergencyContact.patient_id == patient_id)
            .filter(EmergencyContact.is_active == True)
            .order_by(desc(EmergencyContact.is_primary), asc(EmergencyContact.name))
            .all()
        )


emergency_contact = CRUDEmergencyContact(EmergencyContact)
