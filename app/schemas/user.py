from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class UserBase(BaseModel):
    """
    Base User schema with common fields.

    This contains the fields that are shared across different User schemas
    (create, update, read). It doesn't include sensitive fields like password_hash
    or fields that are auto-generated like id."""

    username: str
    email: EmailStr
    full_name: str
    role: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """
        Validate username requirements.

        Args:
            v: The username value to validate

        Returns:
            Cleaned username (lowercase)

        Raises:
            ValueError: If username doesn't meet requirements
        """
        if not v or len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be less than 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower().strip()    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """
        Validate that the role is one of the allowed values.

        Args:
            v: The role value to validate

        Returns:
            Cleaned role (lowercase)

        Raises:
            ValueError: If role is not in allowed list
        """
        allowed_roles = ["admin", "user"]
        if v.lower() not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v.lower()    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        """
        Validate full name requirements.

        Args:
            v: The full name value to validate

        Returns:
            Cleaned full name (stripped whitespace)

        Raises:
            ValueError: If full name is empty or too long
        """
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        if len(v) > 100:
            raise ValueError("Full name must be less than 100 characters")
        return v.strip()


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Includes all fields from UserBase plus the password field.
    This is used when a new user registers or is created by an admin.

    Example:
        user_data = UserCreate(
            username="john_doe",
            email="john@example.com",
            password="secure_password123",
            full_name="John Doe",
            role="user"        )
    """

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """
        Validate password requirements.

        Args:
            v: The password value to validate

        Returns:
            The password (unchanged)

        Raises:
            ValueError: If password doesn't meet security requirements
        """
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")

        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)

        if not (has_letter and has_number):
            raise ValueError("Password must contain at least one letter and one number")

        return v


class UserUpdate(BaseModel):
    """
    Schema for updating an existing user.

    All fields are optional, so users can update only the fields they want to change.
    Note: Password updates should use a separate endpoint for security.

    Example:        update_data = UserUpdate(
            email="newemail@example.com",
            full_name="John Smith"
        )
    """

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username if provided."""
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError("Username must be at least 3 characters long")
            if len(v) > 50:
                raise ValueError("Username must be less than 50 characters")
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError(
                    "Username can only contain letters, numbers, underscores, and hyphens"
                )
            return v.lower().strip()
        return v    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role if provided."""
        if v is not None:
            allowed_roles = ["admin", "user"]
            if v.lower() not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
            return v.lower()
        return v

    @field_validator("full_name")
    def validate_full_name(cls, v):
        """Validate full name if provided."""
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("Full name must be at least 2 characters long")
            if len(v) > 100:
                raise ValueError("Full name must be less than 100 characters")
            return v.strip()
        return v


class User(UserBase):
    """
    Schema for reading/returning user data.

    This includes all the base fields plus the database-generated id field.
    This is what gets returned when fetching user data from the API.
    Note: password_hash is excluded for security.

    Example response:
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "role": "user"
        }
    """

    id: int

    class Config:
        """
        Pydantic configuration.

        from_attributes = True allows Pydantic to work with SQLAlchemy models
        by reading data from attributes instead of expecting a dictionary.
        """

        from_attributes = True


class UserLogin(BaseModel):
    """
    Schema for user login/authentication.

    Simple schema with just username and password for login requests.

    Example:
        login_data = UserLogin(
            username="john_doe",
            password="secure_password123"
        )
    """

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Clean username for login."""
        return v.lower().strip() if v else v


class UserChangePassword(BaseModel):
    """
    Schema for changing a user's password.

    Requires both current and new password for security.

    Example:
        password_change = UserChangePassword(
            current_password="old_password123",
            new_password="new_password456"
        )
    """

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        """Validate the new password using same rules as UserCreate."""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")

        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)

        if not (has_letter and has_number):
            raise ValueError("Password must contain at least one letter and one number")

        return v


class Token(BaseModel):
    """
    Schema for JWT token response.

    Returned when a user successfully logs in.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema for token payload data.

    Used internally for token validation.
    """

    username: Optional[str] = None
