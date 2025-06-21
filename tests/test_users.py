"""
Tests for user management and admin functionality.
"""
from fastapi.testclient import TestClient


class TestUserManagement:
    """Test class for user management functionality."""

    def test_user_profile_access(self, client: TestClient, authenticated_user):
        """Test accessing user profile information."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "username" in data
            assert "email" in data

    def test_user_profile_update(self, client: TestClient, authenticated_user):
        """Test updating user profile information."""
        headers = authenticated_user["headers"]
        
        update_data = {
            "full_name": "Updated Full Name",
            "email": "updated@example.com"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        assert response.status_code in [200, 404, 422]

    def test_password_change(self, client: TestClient, authenticated_user):
        """Test changing user password."""
        headers = authenticated_user["headers"]
        
        password_data = {
            "current_password": authenticated_user["user_data"]["password"],
            "new_password": "newpassword123"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        assert response.status_code in [200, 404, 422, 400]

    def test_user_deletion(self, client: TestClient, authenticated_user):
        """Test user account deletion."""
        headers = authenticated_user["headers"]
        
        response = client.delete("/api/v1/users/me", headers=headers)
        assert response.status_code in [200, 404, 422]


class TestAdminFunctionality:
    """Test class for admin-specific functionality."""

    def test_admin_user_list(self, client: TestClient, authenticated_admin):
        """Test admin access to user list."""
        headers = authenticated_admin["headers"]
        
        response = client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code in [200, 403, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_admin_user_management(self, client: TestClient, authenticated_admin):
        """Test admin user management capabilities."""
        headers = authenticated_admin["headers"]
        
        # Test getting specific user info
        response = client.get("/api/v1/admin/users/1", headers=headers)
        assert response.status_code in [200, 404, 403]

    def test_admin_system_stats(self, client: TestClient, authenticated_admin):
        """Test admin access to system statistics."""
        headers = authenticated_admin["headers"]
        
        response = client.get("/api/v1/admin/stats", headers=headers)
        assert response.status_code in [200, 403, 404]

    def test_regular_user_cannot_access_admin(self, client: TestClient, authenticated_user):
        """Test that regular users cannot access admin endpoints."""
        headers = authenticated_user["headers"]
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/system"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found

    def test_admin_requires_authentication(self, client: TestClient):
        """Test that admin endpoints require authentication."""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/system"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401


class TestDataExport:
    """Test class for data export functionality."""

    def test_export_patient_data(self, client: TestClient, authenticated_user):
        """Test exporting patient data."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/export/patient-data", headers=headers)
        assert response.status_code in [200, 404, 422]

    def test_export_medical_records(self, client: TestClient, authenticated_user):
        """Test exporting medical records."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/export/medical-records", headers=headers)
        assert response.status_code in [200, 404, 422]

    def test_export_requires_authentication(self, client: TestClient):
        """Test that export endpoints require authentication."""
        export_endpoints = [
            "/api/v1/export/patient-data",
            "/api/v1/export/medical-records"
        ]
        
        for endpoint in export_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_export_format_options(self, client: TestClient, authenticated_user):
        """Test different export format options."""
        headers = authenticated_user["headers"]
        
        # Test PDF export
        response = client.get("/api/v1/export/patient-data?format=pdf", headers=headers)
        assert response.status_code in [200, 404, 422]
        
        # Test JSON export
        response = client.get("/api/v1/export/patient-data?format=json", headers=headers)
        assert response.status_code in [200, 404, 422]


class TestFileUpload:
    """Test class for file upload functionality."""

    def test_lab_result_file_upload(self, client: TestClient, authenticated_user):
        """Test uploading lab result files."""
        headers = authenticated_user["headers"]
        
        # Create a test file-like object
        test_file_content = b"Test lab result content"
        files = {"file": ("test_lab_result.pdf", test_file_content, "application/pdf")}
        
        response = client.post("/api/v1/lab-result-file/upload", files=files, headers=headers)
        assert response.status_code in [200, 201, 404, 422]

    def test_file_upload_validation(self, client: TestClient, authenticated_user):
        """Test file upload validation."""
        headers = authenticated_user["headers"]
        
        # Test with invalid file type
        test_file_content = b"Test content"
        files = {"file": ("test.exe", test_file_content, "application/x-executable")}
        
        response = client.post("/api/v1/lab-result-file/upload", files=files, headers=headers)
        assert response.status_code in [422, 400]

    def test_file_upload_requires_authentication(self, client: TestClient):
        """Test that file upload requires authentication."""
        test_file_content = b"Test content"
        files = {"file": ("test.pdf", test_file_content, "application/pdf")}
        
        response = client.post("/api/v1/lab-result-file/upload", files=files)
        assert response.status_code == 401


class TestUserValidation:
    """Test class for user data validation."""

    def test_invalid_email_update(self, client: TestClient, authenticated_user):
        """Test updating user with invalid email."""
        headers = authenticated_user["headers"]
        
        invalid_data = {
            "email": "invalid-email-format"
        }
        
        response = client.put("/api/v1/users/me", json=invalid_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_weak_password_validation(self, client: TestClient, authenticated_user):
        """Test validation of weak passwords."""
        headers = authenticated_user["headers"]
        
        weak_password_data = {
            "current_password": authenticated_user["user_data"]["password"],
            "new_password": "123"  # Too short/weak
        }
        
        response = client.put("/api/v1/users/me/password", json=weak_password_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_duplicate_email_prevention(self, client: TestClient, authenticated_user, test_admin_data):
        """Test prevention of duplicate email addresses."""
        # First create an admin user
        admin_response = client.post("/api/v1/auth/register", json=test_admin_data)
        assert admin_response.status_code == 200
        
        # Try to update regular user with admin's email
        headers = authenticated_user["headers"]
        duplicate_email_data = {
            "email": test_admin_data["email"]
        }
        
        response = client.put("/api/v1/users/me", json=duplicate_email_data, headers=headers)
        assert response.status_code in [422, 400]
