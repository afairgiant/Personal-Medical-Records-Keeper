from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, validator


class ImmunizationBase(BaseModel):
    vaccine_name: str = Field(
        ..., min_length=2, max_length=200, description="Name of the vaccine"
    )
    date_administered: date = Field(
        ..., description="Date when the vaccine was administered"
    )
    dose_number: Optional[int] = Field(
        None, ge=1, description="Dose number in the series"
    )
    lot_number: Optional[str] = Field(
        None, max_length=50, description="Vaccine lot number"
    )
    manufacturer: Optional[str] = Field(
        None, max_length=200, description="Vaccine manufacturer"
    )
    site: Optional[str] = Field(None, max_length=100, description="Injection site")
    route: Optional[str] = Field(
        None, max_length=50, description="Route of administration"
    )
    expiration_date: Optional[date] = Field(None, description="Vaccine expiration date")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    patient_id: int = Field(..., gt=0, description="ID of the patient")
    practitioner_id: Optional[int] = Field(
        None, gt=0, description="ID of the administering practitioner"
    )

    @validator("date_administered", pre=True)
    def validate_date_administered(cls, v):
        if isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        if v > date.today():
            raise ValueError("Administration date cannot be in the future")
        return v

    @validator("expiration_date", pre=True)
    def validate_expiration_date(cls, v, values):
        if v and isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid expiration date format. Use YYYY-MM-DD")
        if v and "date_administered" in values:
            admin_date = values["date_administered"]
            if isinstance(admin_date, str):
                try:
                    admin_date = date.fromisoformat(admin_date)
                except ValueError:
                    pass  # Skip comparison if admin_date is invalid
            if isinstance(admin_date, date) and v < admin_date:
                raise ValueError("Expiration date cannot be before administration date")
        return v

    @validator("route")
    def validate_route(cls, v):
        if v:
            valid_routes = [
                "intramuscular",
                "subcutaneous",
                "intradermal",
                "oral",
                "nasal",
            ]
            if v.lower() not in valid_routes:
                raise ValueError(f"Route must be one of: {', '.join(valid_routes)}")
            return v.lower()
        return v


class ImmunizationCreate(ImmunizationBase):
    patient_id: int


class ImmunizationUpdate(BaseModel):
    vaccine_name: Optional[str] = Field(None, min_length=2, max_length=200)
    date_administered: Optional[date] = None
    dose_number: Optional[int] = Field(None, ge=1)
    lot_number: Optional[str] = Field(None, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=200)
    site: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=50)
    expiration_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    practitioner_id: Optional[int] = Field(None, gt=0)

    @validator("date_administered", pre=True)
    def validate_date_administered(cls, v):
        if v and isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        if v and v > date.today():
            raise ValueError("Administration date cannot be in the future")
        return v

    @validator("expiration_date", pre=True)
    def validate_expiration_date(cls, v, values):
        if v and isinstance(v, str):
            try:
                v = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid expiration date format. Use YYYY-MM-DD")
        if (
            v
            and "date_administered" in values
            and values["date_administered"]
            and v < values["date_administered"]
        ):
            raise ValueError("Expiration date cannot be before administration date")
        return v

    @validator("route")
    def validate_route(cls, v):
        if v:
            valid_routes = [
                "intramuscular",
                "subcutaneous",
                "intradermal",
                "oral",
                "nasal",
            ]
            if v.lower() not in valid_routes:
                raise ValueError(f"Route must be one of: {', '.join(valid_routes)}")
            return v.lower()
        return v


class ImmunizationResponse(ImmunizationBase):
    id: int

    class Config:
        from_attributes = True


class ImmunizationWithRelations(ImmunizationResponse):
    patient: Optional[dict] = None
    practitioner: Optional[dict] = None

    class Config:
        from_attributes = True


class ImmunizationSummary(BaseModel):
    id: int
    vaccine_name: str
    date_administered: date
    dose_number: Optional[int]
    patient_name: Optional[str] = None
    practitioner_name: Optional[str] = None

    class Config:
        from_attributes = True
