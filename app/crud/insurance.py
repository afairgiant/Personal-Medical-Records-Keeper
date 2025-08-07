from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.models import Insurance
from app.schemas.insurance import InsuranceCreate, InsuranceUpdate


class CRUDInsurance(CRUDBase[Insurance, InsuranceCreate, InsuranceUpdate]):
    """
    CRUD operations for Insurance model.

    Provides specialized methods for insurance management including
    patient-specific insurance queries, type filtering, and status management.
    """

    def get_by_patient(
        self, db: Session, *, patient_id: int, skip: int = 0, limit: int = 100
    ) -> List[Insurance]:
        """
        Get all insurance records for a specific patient.

        Args:
            db: Database session
            patient_id: Patient ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of insurance records for the patient
        """
        return self.query(
            db=db,
            filters={"patient_id": patient_id},
            order_by="insurance_type",
            skip=skip,
            limit=limit,
        )

    def get_active_by_patient(
        self, db: Session, *, patient_id: int
    ) -> List[Insurance]:
        """
        Get all active insurance records for a specific patient.

        Args:
            db: Database session
            patient_id: Patient ID to filter by

        Returns:
            List of active insurance records for the patient
        """
        return self.query(
            db=db,
            filters={"patient_id": patient_id, "status": "active"},
            order_by="insurance_type",
        )

    def get_by_type(
        self, db: Session, *, patient_id: int, insurance_type: str
    ) -> List[Insurance]:
        """
        Get insurance records by type for a specific patient.

        Args:
            db: Database session
            patient_id: Patient ID to filter by
            insurance_type: Type of insurance (medical, dental, vision, prescription)

        Returns:
            List of insurance records of the specified type
        """
        return self.query(
            db=db,
            filters={"patient_id": patient_id, "insurance_type": insurance_type},
            order_by="created_at",
        )

    def get_primary_medical(
        self, db: Session, *, patient_id: int
    ) -> Optional[Insurance]:
        """
        Get the primary medical insurance for a patient.

        Args:
            db: Database session
            patient_id: Patient ID to filter by

        Returns:
            Primary medical insurance record or None
        """
        return (
            db.query(Insurance)
            .filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.insurance_type == "medical",
                    Insurance.is_primary == True,
                    Insurance.status == "active"
                )
            )
            .first()
        )

    def get_by_status(
        self, db: Session, *, patient_id: int, status: str
    ) -> List[Insurance]:
        """
        Get insurance records by status for a specific patient.

        Args:
            db: Database session
            patient_id: Patient ID to filter by
            status: Insurance status (active, inactive, expired, pending)

        Returns:
            List of insurance records with the specified status
        """
        return self.query(
            db=db,
            filters={"patient_id": patient_id, "status": status},
            order_by="insurance_type",
        )

    def update_status(
        self, db: Session, *, insurance_id: int, status: str
    ) -> Optional[Insurance]:
        """
        Update the status of an insurance record.

        Args:
            db: Database session
            insurance_id: Insurance record ID
            status: New status value

        Returns:
            Updated insurance record or None if not found
        """
        insurance = self.get(db, id=insurance_id)
        if insurance:
            return self.update(db, db_obj=insurance, obj_in={"status": status})
        return None

    def set_primary(
        self, db: Session, *, patient_id: int, insurance_id: int
    ) -> Optional[Insurance]:
        """
        Set an insurance record as primary and unset all others for the same type.

        Args:
            db: Database session
            patient_id: Patient ID
            insurance_id: Insurance record ID to set as primary

        Returns:
            Updated insurance record or None if not found
        """
        insurance = self.get(db, id=insurance_id)
        if insurance and insurance.patient_id == patient_id:
            # First, unset all other primary insurances of the same type
            db.query(Insurance).filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.insurance_type == insurance.insurance_type,
                    Insurance.id != insurance_id
                )
            ).update({"is_primary": False})
            
            # Set this insurance as primary
            return self.update(db, db_obj=insurance, obj_in={"is_primary": True})
        
        return None

    def get_expiring_soon(
        self, db: Session, *, patient_id: int, days: int = 30
    ) -> List[Insurance]:
        """
        Get insurance records that expire within the specified number of days.

        Args:
            db: Database session
            patient_id: Patient ID to filter by
            days: Number of days ahead to check for expiration

        Returns:
            List of insurance records expiring soon
        """
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=days)
        
        return (
            db.query(Insurance)
            .filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.status == "active",
                    Insurance.expiration_date.is_not(None),
                    Insurance.expiration_date <= future_date
                )
            )
            .order_by(Insurance.expiration_date)
            .all()
        )

    def search_by_company(
        self, db: Session, *, patient_id: int, company_name: str
    ) -> List[Insurance]:
        """
        Search insurance records by company name (partial match).

        Args:
            db: Database session
            patient_id: Patient ID to filter by
            company_name: Company name to search for

        Returns:
            List of insurance records matching the company name
        """
        return (
            db.query(Insurance)
            .filter(
                and_(
                    Insurance.patient_id == patient_id,
                    Insurance.company_name.ilike(f"%{company_name}%")
                )
            )
            .order_by(Insurance.company_name)
            .all()
        )


# Create the global insurance CRUD instance
insurance = CRUDInsurance(Insurance)