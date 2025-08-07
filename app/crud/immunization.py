from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.models import Immunization
from app.schemas.immunization import ImmunizationCreate, ImmunizationUpdate


class CRUDImmunization(CRUDBase[Immunization, ImmunizationCreate, ImmunizationUpdate]):
    """
    Immunization-specific CRUD operations for vaccine records.

    Handles patient immunization records, vaccine tracking, and schedules.
    """

    def create(self, db: Session, *, obj_in: ImmunizationCreate) -> Immunization:
        """
        Create a new immunization record.

        Override base create method to properly handle date fields without jsonable_encoder.
        """
        # Convert Pydantic model to dict while preserving date objects
        # Handle both Pydantic v1 and v2 compatibility, and plain dictionaries
        if isinstance(obj_in, dict):
            obj_data = obj_in.copy()
        elif hasattr(obj_in, "model_dump"):
            obj_data = obj_in.model_dump()
        else:
            obj_data = obj_in.dict()

        # Create the database object directly from the dict
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Immunization, obj_in: ImmunizationUpdate
    ) -> Immunization:
        """
        Update an immunization record.

        Override base update method to properly handle date fields without jsonable_encoder.
        """
        # Get the data as dict, excluding None values
        # Handle both Pydantic v1 and v2 compatibility
        if hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Update the database object
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_vaccine(
        self, db: Session, *, vaccine_name: str, patient_id: Optional[int] = None
    ) -> List[Immunization]:
        """
        Retrieve immunizations by vaccine name, optionally filtered by patient.

        Args:
            db: SQLAlchemy database session
            vaccine_name: Name of the vaccine
            patient_id: Optional patient ID to filter by

        Returns:
            List of immunizations for the specified vaccine
        """
        filters: Dict[str, Any] = {}
        if patient_id:
            filters["patient_id"] = patient_id

        return self.query(
            db=db,
            filters=filters,
            search={"field": "vaccine_name", "term": vaccine_name},
            order_by="date_administered",
            order_desc=True,
        )

    def get_recent_immunizations(
        self, db: Session, *, patient_id: int, days: int = 365
    ) -> List[Immunization]:
        """
        Get recent immunizations for a patient within specified days.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient
            days: Number of days to look back

        Returns:
            List of recent immunizations
        """
        from app.crud.utils import get_recent_records

        return get_recent_records(
            db=db,
            model=self.model,
            date_field="date_administered",
            days=days,
            patient_id=patient_id,
            order_by="date_administered",
            order_desc=True,
        )

    def get_due_for_booster(
        self,
        db: Session,
        *,
        patient_id: int,
        vaccine_name: str,
        months_interval: int = 12,
    ) -> bool:
        """
        Check if a patient is due for a booster shot.

        Args:
            db: SQLAlchemy database session
            patient_id: ID of the patient
            vaccine_name: Name of the vaccine
            months_interval: Months between doses

        Returns:
            True if due for booster, False otherwise
        """
        from datetime import date, timedelta

        # Get latest dose using our generic search method
        last_doses = self.query(
            db=db,
            filters={"patient_id": patient_id},
            search={"field": "vaccine_name", "term": vaccine_name},
            order_by="date_administered",
            order_desc=True,
            limit=1,
        )

        if not last_doses:
            return True  # Never vaccinated

        last_dose = last_doses[0]

        # Convert to actual date value for comparison
        last_dose_date = last_dose.date_administered
        if hasattr(last_dose_date, "date"):
            last_dose_date = last_dose_date.date()

        due_date = last_dose_date + timedelta(days=months_interval * 30)
        return bool(date.today() >= due_date)


# Create the immunization CRUD instance
immunization = CRUDImmunization(Immunization)
