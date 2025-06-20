from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.models import Allergy
from app.schemas.allergy import AllergyCreate, AllergyUpdate


class CRUDAllergy(CRUDBase[Allergy, AllergyCreate, AllergyUpdate]):
    """
    Allergy-specific CRUD operations for patient allergies.

    Handles patient allergy records, allergen tracking, and severity management.
    """

    def get_by_patient(
        self, db: Session, *, patient_id: int, skip: int = 0, limit: int = 100
    ) -> List[Allergy]:
        """
        Retrieve all allergies for a specific patient.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of allergies for the patient
        """
        return (
            db.query(Allergy)
            .filter(Allergy.patient_id == patient_id)
            .order_by(Allergy.onset_date.desc().nullslast())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_severity(
        self, db: Session, *, severity: str, patient_id: Optional[int] = None
    ) -> List[Allergy]:
        """
        Retrieve allergies by severity, optionally filtered by patient.

        Args:
            db: SQLAlchemy database session
            severity: Severity to filter by
            patient_id: Optional patient ID to filter by

        Returns:
            List of allergies with the specified severity
        """
        query = db.query(Allergy).filter(Allergy.severity == severity.lower())

        if patient_id:
            query = query.filter(Allergy.patient_id == patient_id)

        return query.order_by(Allergy.onset_date.desc().nullslast()).all()

    def get_active_allergies(self, db: Session, *, patient_id: int) -> List[Allergy]:
        """
        Get all active allergies for a patient.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient

        Returns:
            List of active allergies
        """
        return (
            db.query(Allergy)
            .filter(Allergy.patient_id == patient_id, Allergy.status == "active")
            .order_by(Allergy.severity.desc(), Allergy.onset_date.desc().nullslast())
            .all()
        )

    def get_critical_allergies(self, db: Session, *, patient_id: int) -> List[Allergy]:
        """
        Get critical (severe and life-threatening) allergies for a patient.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient

        Returns:
            List of critical allergies
        """
        return (
            db.query(Allergy)
            .filter(
                Allergy.patient_id == patient_id,
                Allergy.status == "active",
                Allergy.severity.in_(["severe", "life-threatening"]),
            )
            .order_by(Allergy.severity.desc(), Allergy.onset_date.desc().nullslast())
            .all()
        )

    def get_by_allergen(
        self, db: Session, *, allergen: str, patient_id: Optional[int] = None
    ) -> List[Allergy]:
        """
        Retrieve allergies by allergen name, optionally filtered by patient.

        Args:
            db: SQLAlchemy database session
            allergen: Allergen name to search for
            patient_id: Optional patient ID to filter by

        Returns:
            List of allergies matching the allergen
        """
        query = db.query(Allergy).filter(Allergy.allergen.ilike(f"%{allergen}%"))

        if patient_id:
            query = query.filter(Allergy.patient_id == patient_id)

        return query.order_by(
            Allergy.severity.desc(), Allergy.onset_date.desc().nullslast()
        ).all()

    def get_with_relations(self, db: Session, allergy_id: int) -> Optional[Allergy]:
        """
        Retrieve an allergy with all related information loaded.

        Args:
            db: SQLAlchemy database session
            allergy_id: ID of the allergy

        Returns:
            Allergy with patient relationship loaded
        """
        return (
            db.query(Allergy)
            .options(joinedload(Allergy.patient))
            .filter(Allergy.id == allergy_id)
            .first()
        )

    def check_allergen_conflict(
        self, db: Session, *, patient_id: int, allergen: str
    ) -> bool:
        """
        Check if a patient has any active allergies to a specific allergen.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient
            allergen: Allergen to check for

        Returns:
            True if patient has active allergy to the allergen, False otherwise
        """
        allergy = (
            db.query(Allergy)
            .filter(
                Allergy.patient_id == patient_id,
                Allergy.status == "active",
                Allergy.allergen.ilike(f"%{allergen}%"),
            )
            .first()
        )
        return allergy is not None


# Create the allergy CRUD instance
allergy = CRUDAllergy(Allergy)
