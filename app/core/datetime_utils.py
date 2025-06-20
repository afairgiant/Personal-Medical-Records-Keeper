"""
Datetime Utility Module

This module provides utilities for handling datetime conversions and validations
across the Medical Records Management System.
"""

from datetime import datetime, date, timezone
from typing import Optional, Union, Any
import re


def get_utc_now() -> datetime:
    """
    Get the current UTC datetime with timezone awareness.
    
    This replaces the deprecated datetime.utcnow() with a timezone-aware alternative.
    """
    return datetime.now(timezone.utc)


def parse_datetime_string(datetime_str: str) -> datetime:
    """
    Parse a datetime string into a Python datetime object.

    Supports multiple common datetime formats:
    - ISO format: "2024-01-15T10:30:00"
    - ISO with microseconds: "2024-01-15T10:30:00.123456"
    - ISO with timezone: "2024-01-15T10:30:00Z"
    - Simple format: "2024-01-15 10:30:00"

    Args:
        datetime_str: String representation of datetime

    Returns:
        Python datetime object

    Raises:
        ValueError: If the datetime string format is not supported

    Examples:
        >>> parse_datetime_string("2024-01-15T10:30:00")
        datetime(2024, 1, 15, 10, 30)

        >>> parse_datetime_string("2024-01-15 10:30:00")
        datetime(2024, 1, 15, 10, 30)
    """
    if not isinstance(datetime_str, str):
        raise ValueError(f"Expected string, got {type(datetime_str)}")

    # Remove timezone info if present (Z or +00:00)
    clean_str = re.sub(
        r"[Z]$|[+-]\d{2}:\d{2}$", "", datetime_str.strip()
    )  # List of supported formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds
        "%Y-%m-%dT%H:%M:%S",  # ISO format
        "%Y-%m-%d %H:%M:%S.%f",  # Simple with microseconds
        "%Y-%m-%d %H:%M:%S",  # Simple format
        "%Y-%m-%dT%H:%M",  # ISO without seconds
        "%Y-%m-%d %H:%M",  # Simple without seconds
        "%Y-%m-%d",  # Date-only format (convert to datetime at midnight)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported datetime format: {datetime_str}")


def ensure_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Ensure a value is converted to a datetime object if possible.

    Args:
        value: String, datetime object, or None

    Returns:
        datetime object or None

    Examples:
        >>> ensure_datetime("2024-01-15T10:30:00")
        datetime(2024, 1, 15, 10, 30)

        >>> ensure_datetime(None)
        None

        >>> ensure_datetime(datetime(2024, 1, 15))
        datetime(2024, 1, 15)
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        if not value.strip():
            return None
        return parse_datetime_string(value)

    raise ValueError(f"Cannot convert {type(value)} to datetime")


def parse_date_string(date_str: str) -> date:
    """
    Parse a date string into a Python date object.

    Args:
        date_str: String representing a date

    Returns:
        date object

    Raises:
        ValueError: If the string cannot be parsed as a date

    Examples:
        >>> parse_date_string("2024-01-15")
        date(2024, 1, 15)
    """
    if not isinstance(date_str, str):
        raise ValueError(f"Expected string, got {type(date_str)}")

    clean_str = date_str.strip()

    # List of supported date formats
    formats = [
        "%Y-%m-%d",  # ISO date format
        "%m/%d/%Y",  # US format
        "%d/%m/%Y",  # European format
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO datetime (extract date part)
        "%Y-%m-%dT%H:%M:%S",  # ISO datetime without microseconds
    ]

    for fmt in formats:
        try:
            if "T" in fmt:
                # For datetime formats, parse as datetime then extract date
                dt = datetime.strptime(clean_str.split("T")[0], "%Y-%m-%d")
                return dt.date()
            else:
                dt = datetime.strptime(clean_str, fmt)
                return dt.date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {date_str}")


def ensure_date(value: Union[str, date, datetime, None]) -> Optional[date]:
    """
    Ensure a value is converted to a date object if possible.

    Args:
        value: String, date object, datetime object, or None

    Returns:
        date object or None

    Examples:
        >>> ensure_date("2024-01-15")
        date(2024, 1, 15)

        >>> ensure_date(None)
        None

        >>> ensure_date(datetime(2024, 1, 15, 10, 30))
        date(2024, 1, 15)
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        if not value.strip():
            return None
        return parse_date_string(value)

    raise ValueError(f"Cannot convert {type(value)} to date")


def convert_date_fields(data: dict, date_fields: list) -> dict:
    """
    Convert specified date fields in a dictionary from strings to date objects.

    Args:
        data: Dictionary containing the data
        date_fields: List of field names that should be converted to date

    Returns:
        Dictionary with converted date fields

    Examples:
        >>> data = {"name": "Test", "birthDate": "2024-01-15"}
        >>> convert_date_fields(data, ["birthDate"])
        {"name": "Test", "birthDate": date(2024, 1, 15)}
    """
    converted_data = data.copy()

    for field in date_fields:
        if field in converted_data:
            try:
                converted_data[field] = ensure_date(converted_data[field])
            except ValueError as e:
                raise ValueError(f"Error converting field '{field}': {e}")

    return converted_data


def convert_datetime_fields(data: dict, datetime_fields: list) -> dict:
    """
    Convert specified datetime fields in a dictionary from strings to datetime objects.

    Args:
        data: Dictionary containing the data
        datetime_fields: List of field names that should be converted to datetime

    Returns:
        Dictionary with converted datetime fields

    Examples:
        >>> data = {"name": "Test", "created_at": "2024-01-15T10:30:00"}
        >>> convert_datetime_fields(data, ["created_at"])
        {"name": "Test", "created_at": datetime(2024, 1, 15, 10, 30)}
    """
    converted_data = data.copy()

    for field in datetime_fields:
        if field in converted_data:
            try:
                converted_data[field] = ensure_datetime(converted_data[field])
            except ValueError as e:
                raise ValueError(f"Error converting field '{field}': {e}")

    return converted_data


def validate_datetime_order(start_field: str, end_field: str, data: dict) -> None:
    """
    Validate that start datetime is before end datetime.

    Args:
        start_field: Name of the start datetime field
        end_field: Name of the end datetime field
        data: Dictionary containing the datetime fields

    Raises:
        ValueError: If end datetime is before start datetime

    Examples:
        >>> data = {"start": datetime(2024, 1, 15), "end": datetime(2024, 1, 16)}
        >>> validate_datetime_order("start", "end", data)  # No error

        >>> data = {"start": datetime(2024, 1, 16), "end": datetime(2024, 1, 15)}
        >>> validate_datetime_order("start", "end", data)  # Raises ValueError
    """
    start_dt = data.get(start_field)
    end_dt = data.get(end_field)

    if start_dt and end_dt:
        if isinstance(start_dt, str):
            start_dt = ensure_datetime(start_dt)
        if isinstance(end_dt, str):
            end_dt = ensure_datetime(end_dt)

        if start_dt and end_dt and end_dt < start_dt:
            raise ValueError(f"{end_field} cannot be before {start_field}")


class DateTimeConverter:
    """
    A reusable datetime converter class for specific use cases.
    """

    def __init__(self, datetime_fields: list):
        """
        Initialize with list of datetime fields to convert.

        Args:
            datetime_fields: List of field names that contain datetime values
        """
        self.datetime_fields = datetime_fields

    def convert(self, data: dict) -> dict:
        """
        Convert datetime fields in the provided data.

        Args:
            data: Dictionary containing data to convert

        Returns:
            Dictionary with converted datetime fields
        """
        return convert_datetime_fields(data, self.datetime_fields)

    def convert_model_data(self, obj_in: Any) -> dict:
        """
        Convert datetime fields from a Pydantic model or dict.

        Args:
            obj_in: Pydantic model instance or dictionary

        Returns:
            Dictionary with converted datetime fields
        """
        if hasattr(obj_in, "dict"):
            # Pydantic model
            data = obj_in.dict()
        elif isinstance(obj_in, dict):
            data = obj_in
        else:
            raise ValueError(f"Unsupported data type: {type(obj_in)}")

        return self.convert(data)


class DateConverter:
    """
    A reusable date converter class for specific use cases.
    """

    def __init__(self, date_fields: list):
        """
        Initialize with list of date fields to convert.

        Args:
            date_fields: List of field names that contain date values
        """
        self.date_fields = date_fields

    def convert(self, data: dict) -> dict:
        """
        Convert date fields in the provided data.

        Args:
            data: Dictionary containing data to convert

        Returns:
            Dictionary with converted date fields
        """
        return convert_date_fields(data, self.date_fields)

    def convert_model_data(self, obj_in: Any) -> dict:
        """
        Convert date fields from a Pydantic model or dict.

        Args:
            obj_in: Pydantic model instance or dictionary

        Returns:
            Dictionary with converted date fields
        """
        if hasattr(obj_in, "dict"):
            # Pydantic model
            data = obj_in.dict()
        elif isinstance(obj_in, dict):
            data = obj_in
        else:
            raise ValueError(f"Unsupported data type: {type(obj_in)}")

        return self.convert(data)


# Pre-configured converters for common models
LAB_RESULT_CONVERTER = DateTimeConverter(
    ["ordered_date", "completed_date", "created_at", "updated_at"]
)

USER_CONVERTER = DateTimeConverter(["created_at", "updated_at", "last_login"])

PATIENT_CONVERTER = DateTimeConverter(["created_at", "updated_at"])

PATIENT_DATE_CONVERTER = DateConverter(["birthDate"])

FILE_CONVERTER = DateTimeConverter(["uploaded_at", "created_at", "updated_at"])
