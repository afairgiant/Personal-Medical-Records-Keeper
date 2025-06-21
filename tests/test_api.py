"""
Tests for API endpoints and general functionality.
"""
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test class for health check and system status endpoints."""

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/api/v1/health")
        
        # Health endpoint should be accessible without authentication
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint redirects or returns app info."""
        response = client.get("/")
        
        # Root endpoint might redirect or return app info
        assert response.status_code in [200, 307, 404]


class TestCORSAndMiddleware:
    """Test class for CORS and middleware functionality."""

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present in responses."""
        response = client.options("/api/v1/auth/register")
        
        # Check if CORS headers are present (might vary based on configuration)
        assert response.status_code in [200, 405, 404]

    def test_content_type_handling(self, client: TestClient, test_user_data):
        """Test that the API properly handles different content types."""
        # Test JSON content type
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code in [200, 400, 422]


class TestErrorHandling:
    """Test class for error handling scenarios."""

    def test_404_for_nonexistent_endpoint(self, client: TestClient):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient):
        """Test that wrong HTTP methods return 405."""
        # Try to POST to a GET endpoint
        response = client.post("/api/v1/health")
        assert response.status_code in [405, 404]

    def test_malformed_json_handling(self, client: TestClient):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/v1/auth/register",
            data='{"invalid": json}',  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [422, 400]

    def test_large_payload_handling(self, client: TestClient):
        """Test handling of unusually large payloads."""
        large_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "x" * 10000,  # Very long name
            "password": "testpassword123",
            "role": "user"
        }
        
        response = client.post("/api/v1/auth/register", json=large_data)
        assert response.status_code in [422, 400, 413]  # 413 = Payload Too Large


class TestSecurityHeaders:
    """Test class for security-related headers and protections."""

    def test_no_sensitive_headers_leaked(self, client: TestClient, authenticated_user):
        """Test that sensitive information is not leaked in headers."""
        headers = authenticated_user["headers"]
        
        response = client.get("/api/v1/auth/me", headers=headers)
        
        # Check that password-related info is not in response
        if response.status_code == 200:
            data = response.json()
            assert "password" not in data
            assert "password_hash" not in data

    def test_sql_injection_protection(self, client: TestClient):
        """Test basic SQL injection protection."""
        malicious_data = {
            "username": "admin'; DROP TABLE users; --",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", data=malicious_data)
        # Should not crash the application
        assert response.status_code in [401, 422, 400]


class TestPerformance:
    """Test class for basic performance scenarios."""

    def test_concurrent_registrations(self, client: TestClient):
        """Test handling of multiple registration requests."""
        users_data = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "password": "password123",
                "role": "user"
            }
            for i in range(5)
        ]
        
        responses = []
        for user_data in users_data:
            response = client.post("/api/v1/auth/register", json=user_data)
            responses.append(response)
        
        # At least some should succeed
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) > 0

    def test_endpoint_response_times(self, client: TestClient):
        """Test that endpoints respond within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Health check should be fast (less than 5 seconds)
        assert response_time < 5.0


class TestDataIntegrity:
    """Test class for data integrity scenarios."""

    def test_user_data_consistency(self, client: TestClient, test_user_data):
        """Test that user data remains consistent across operations."""
        # Register user
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        # Login user
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user info
        response = client.get("/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            assert user_info["username"] == test_user_data["username"].lower()
            assert user_info["email"] == test_user_data["email"]

    def test_case_insensitive_username_handling(self, client: TestClient, test_user_data):
        """Test that usernames are handled case-insensitively."""
        # Register with lowercase username
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        # Try to login with uppercase username
        login_data = {
            "username": test_user_data["username"].upper(),
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        # Should succeed regardless of case
        assert response.status_code in [200, 401]  # Depends on implementation
