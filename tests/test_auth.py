"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthenticationEndpoints:
    """Test class for authentication-related endpoints."""

    def test_register_user_success(self, client: TestClient, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"].lower()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert "password" not in data  # Password should not be returned

    def test_register_user_duplicate_username(self, client: TestClient, test_user_data):
        """Test registration fails with duplicate username."""
        # First registration should succeed
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        # Second registration with same username should fail
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400

    def test_register_user_duplicate_email(self, client: TestClient, test_user_data):
        """Test registration fails with duplicate email."""
        # First registration
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        # Second registration with different username but same email
        duplicate_email_data = test_user_data.copy()
        duplicate_email_data["username"] = "differentuser"
        response = client.post("/api/v1/auth/register", json=duplicate_email_data)
        assert response.status_code == 400

    def test_register_user_invalid_email(self, client: TestClient, test_user_data):
        """Test registration fails with invalid email."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_register_user_short_username(self, client: TestClient, test_user_data):
        """Test registration fails with username too short."""
        invalid_data = test_user_data.copy()
        invalid_data["username"] = "ab"  # Too short
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_register_user_invalid_role(self, client: TestClient, test_user_data):
        """Test registration fails with invalid role."""
        invalid_data = test_user_data.copy()
        invalid_data["role"] = "invalid_role"
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_login_success(self, client: TestClient, test_user_data):
        """Test successful user login."""
        # First register a user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Then try to login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, client: TestClient):
        """Test login fails with invalid username."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401

    def test_login_invalid_password(self, client: TestClient, test_user_data):
        """Test login fails with invalid password."""
        # Register a user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401

    def test_logout_success(self, client: TestClient, authenticated_user):
        """Test successful user logout."""
        headers = authenticated_user["headers"]
        
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_logout_without_token(self, client: TestClient):
        """Test logout fails without authentication token."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_current_user(self, client: TestClient, authenticated_user):
        """Test getting current user information."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == authenticated_user["user_data"]["username"].lower()
        assert data["email"] == authenticated_user["user_data"]["email"]

    def test_current_user_without_token(self, client: TestClient):
        """Test getting current user fails without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_access_protected_endpoint_with_valid_token(self, client: TestClient, authenticated_user):
        """Test accessing a protected endpoint with valid token."""
        headers = authenticated_user["headers"]
        
        # Try to access a protected endpoint (patients/me)
        response = client.get("/api/v1/patients/me", headers=headers)
        # Should not return 401 (unauthorized)
        assert response.status_code != 401

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing a protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/patients/me", headers=headers)
        assert response.status_code == 401

    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing a protected endpoint without token."""
        response = client.get("/api/v1/patients/me")
        assert response.status_code == 401
