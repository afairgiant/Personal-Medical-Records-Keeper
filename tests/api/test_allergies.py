"""
Tests for Allergies API endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.schemas.patient import PatientCreate
from tests.utils.user import create_random_user, create_token_headers_for_user


class TestAllergiesAPI:
    """Test Allergies API endpoints."""

    @pytest.fixture
    def user_with_patient(self, db_session: Session):
        """Create a user with patient record for testing."""
        user_data = create_random_user(db_session)
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date="1990-01-01",
            gender="M",
            address="123 Main St"
        )
        patient = patient_crud.create_for_user(
            db_session, user_id=user_data["user"].id, patient_data=patient_data
        )
        return {**user_data, "patient": patient}

    @pytest.fixture
    def authenticated_headers(self, user_with_patient):
        """Create authentication headers."""
        return create_token_headers_for_user(user_with_patient["user"])

    def test_create_allergy_success(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test successful allergy creation."""
        allergy_data = {
            "allergen": "Penicillin",
            "severity": "severe",
            "reaction": "Anaphylaxis, difficulty breathing, hives",
            "onset_date": "2023-05-15",
            "status": "active",
            "notes": "Confirmed by allergist Dr. Smith",
            "treatment": "Epinephrine auto-injector prescribed"
        }

        response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["allergen"] == "Penicillin"
        assert data["severity"] == "severe"
        assert data["reaction"] == "Anaphylaxis, difficulty breathing, hives"
        assert data["status"] == "active"
        assert data["patient_id"] == user_with_patient["patient"].id

    def test_create_critical_allergy(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test creating a life-threatening allergy."""
        allergy_data = {
            "allergen": "Peanuts",
            "severity": "life-threatening",
            "reaction": "Severe anaphylaxis within minutes",
            "onset_date": "2020-03-10",
            "status": "active",
            "notes": "Patient carries EpiPen at all times",
            "verified_by": "Emergency Department - City Hospital"
        }

        response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["allergen"] == "Peanuts"
        assert data["severity"] == "life-threatening"
        assert data["status"] == "active"

    def test_get_allergies_list(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting list of allergies."""
        # Create multiple allergies
        allergies = [
            {
                "allergen": "Penicillin",
                "severity": "severe",
                "reaction": "Rash, swelling",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Shellfish",
                "severity": "moderate",
                "reaction": "Hives, stomach upset",
                "onset_date": "2022-08-20",
                "status": "active"
            },
            {
                "allergen": "Latex",
                "severity": "mild",
                "reaction": "Contact dermatitis",
                "onset_date": "2021-06-10",
                "status": "inactive"
            }
        ]

        for allergy_data in allergies:
            client.post(
                "/api/v1/allergies/",
                json=allergy_data,
                headers=authenticated_headers
            )

        # Get allergies list
        response = client.get("/api/v1/allergies/", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

        # Should include all created allergies
        allergens = [allergy["allergen"] for allergy in data]
        assert "Penicillin" in allergens
        assert "Shellfish" in allergens
        assert "Latex" in allergens

    def test_get_active_allergies_only(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test filtering for active allergies only."""
        # Create active and inactive allergies
        allergies = [
            {
                "allergen": "Active Allergen",
                "severity": "severe",
                "reaction": "Severe reaction",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Inactive Allergen",
                "severity": "mild",
                "reaction": "Mild reaction",
                "onset_date": "2022-01-15",
                "status": "inactive"
            }
        ]

        for allergy_data in allergies:
            client.post(
                "/api/v1/allergies/",
                json=allergy_data,
                headers=authenticated_headers
            )

        # Get only active allergies
        response = client.get(
            "/api/v1/allergies/?status=active",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        
        # Filter the response to only include ones we created
        created_allergens = [allergy for allergy in data if allergy["allergen"] in ["Active Allergen", "Inactive Allergen"]]
        assert len(created_allergens) == 1
        assert created_allergens[0]["status"] == "active"
        assert created_allergens[0]["allergen"] == "Active Allergen"

    def test_get_critical_allergies(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test filtering for critical (severe/life-threatening) allergies."""
        # Create allergies with different severities
        allergies = [
            {
                "allergen": "Life Threatening Drug",
                "severity": "life-threatening",
                "reaction": "Anaphylaxis",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Severe Drug",
                "severity": "severe",
                "reaction": "Severe reaction",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Mild Allergen",
                "severity": "mild",
                "reaction": "Mild reaction",
                "onset_date": "2023-01-15",
                "status": "active"
            }
        ]

        for allergy_data in allergies:
            client.post(
                "/api/v1/allergies/",
                json=allergy_data,
                headers=authenticated_headers
            )

        # Get severe allergies
        response = client.get(
            "/api/v1/allergies/?severity=severe",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        severe_allergies = [allergy for allergy in data if allergy["allergen"] == "Severe Drug"]
        assert len(severe_allergies) == 1

        # Get life-threatening allergies  
        response = client.get(
            "/api/v1/allergies/?severity=life-threatening",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        critical_allergies = [allergy for allergy in data if allergy["allergen"] == "Life Threatening Drug"]
        assert len(critical_allergies) == 1

    def test_get_allergy_by_id(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test getting a specific allergy by ID."""
        allergy_data = {
            "allergen": "Sulfa Drugs",
            "severity": "moderate",
            "reaction": "Skin rash, nausea",
            "onset_date": "2023-01-15",
            "status": "active",
            "notes": "Reaction occurred during antibiotic treatment"
        }

        create_response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        allergy_id = create_response.json()["id"]

        # Get allergy by ID
        response = client.get(
            f"/api/v1/allergies/{allergy_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == allergy_id
        assert data["allergen"] == "Sulfa Drugs"
        assert data["severity"] == "moderate"

    def test_update_allergy(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test updating an allergy."""
        # Create allergy
        allergy_data = {
            "allergen": "Iodine",
            "severity": "moderate",
            "reaction": "Rash",
            "onset_date": "2023-01-15",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        allergy_id = create_response.json()["id"]

        # Update allergy with more severe reaction
        update_data = {
            "severity": "severe",
            "reaction": "Severe rash, difficulty breathing, swelling",
            "notes": "Reaction severity increased after recent exposure",
            "verified_by": "Dr. Johnson - Allergy Specialist"
        }

        response = client.put(
            f"/api/v1/allergies/{allergy_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "severe"
        assert data["reaction"] == "Severe rash, difficulty breathing, swelling"
        assert data["notes"] == "Reaction severity increased after recent exposure"
        assert data["allergen"] == "Iodine"  # Unchanged

    def test_deactivate_allergy(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test deactivating an allergy."""
        # Create active allergy
        allergy_data = {
            "allergen": "Temporary Allergen",
            "severity": "mild",
            "reaction": "Mild rash",
            "onset_date": "2023-01-15",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        allergy_id = create_response.json()["id"]

        # Deactivate allergy
        update_data = {
            "status": "inactive",
            "notes": "Allergy resolved after treatment"
        }

        response = client.put(
            f"/api/v1/allergies/{allergy_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"
        assert data["notes"] == "Allergy resolved after treatment"

    def test_delete_allergy(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test deleting an allergy."""
        allergy_data = {
            "allergen": "Test Allergen to Delete",
            "severity": "mild",
            "reaction": "Test reaction",
            "onset_date": "2023-01-15",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=authenticated_headers
        )

        allergy_id = create_response.json()["id"]

        # Delete allergy
        response = client.delete(
            f"/api/v1/allergies/{allergy_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/v1/allergies/{allergy_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    def test_allergy_search_by_allergen(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test searching allergies by allergen name."""
        # Create allergies with different allergens
        allergies = [
            {
                "allergen": "Penicillin G",
                "severity": "severe",
                "reaction": "Anaphylaxis",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Amoxicillin",
                "severity": "moderate",
                "reaction": "Rash",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Shellfish",
                "severity": "mild",
                "reaction": "Stomach upset",
                "onset_date": "2023-01-15",
                "status": "active"
            }
        ]

        for allergy_data in allergies:
            client.post(
                "/api/v1/allergies/",
                json=allergy_data,
                headers=authenticated_headers
            )

        # Search for allergies containing "cillin"
        response = client.get(
            "/api/v1/allergies/?search=cillin",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        
        # Filter to only our test allergies
        cillin_allergies = [allergy for allergy in data if "cillin" in allergy["allergen"]]
        assert len(cillin_allergies) == 2
        
        allergens = [allergy["allergen"] for allergy in cillin_allergies]
        assert "Penicillin G" in allergens
        assert "Amoxicillin" in allergens

    def test_allergy_patient_isolation(self, client: TestClient, db_session: Session):
        """Test that users can only access their own allergies."""
        # Create two users with patients
        user1_data = create_random_user(db_session)
        patient1_data = PatientCreate(
            first_name="User",
            last_name="One",
            birth_date="1990-01-01",
            gender="M"
        )
        patient1 = patient_crud.create_for_user(
            db_session, user_id=user1_data["user"].id, patient_data=patient1_data
        )
        headers1 = create_token_headers_for_user(user1_data["user"])

        user2_data = create_random_user(db_session)
        patient2_data = PatientCreate(
            first_name="User",
            last_name="Two",
            birth_date="1990-01-01",
            gender="F"
        )
        patient2 = patient_crud.create_for_user(
            db_session, user_id=user2_data["user"].id, patient_data=patient2_data
        )
        headers2 = create_token_headers_for_user(user2_data["user"])

        # User1 creates an allergy
        allergy_data = {
            "allergen": "Private Allergen",
            "severity": "severe",
            "reaction": "Confidential reaction",
            "onset_date": "2023-01-15",
            "status": "active"
        }

        create_response = client.post(
            "/api/v1/allergies/",
            json=allergy_data,
            headers=headers1
        )

        allergy_id = create_response.json()["id"]

        # User2 tries to access User1's allergy - should fail
        response = client.get(
            f"/api/v1/allergies/{allergy_id}",
            headers=headers2
        )
        assert response.status_code == 404

        # User2 tries to update User1's allergy - should fail
        update_response = client.put(
            f"/api/v1/allergies/{allergy_id}",
            json={"severity": "mild"},
            headers=headers2
        )
        assert update_response.status_code == 404

    def test_allergy_validation_errors(self, client: TestClient, authenticated_headers):
        """Test various validation error scenarios."""
        # Test missing required fields
        invalid_data = {
            "severity": "severe",
            "reaction": "Some reaction"
            # Missing allergen
        }

        response = client.post(
            "/api/v1/allergies/",
            json=invalid_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid severity
        invalid_severity_data = {
            "allergen": "Test Allergen",
            "severity": "invalid_severity",
            "reaction": "Test reaction"
        }

        response = client.post(
            "/api/v1/allergies/",
            json=invalid_severity_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid status
        invalid_status_data = {
            "allergen": "Test Allergen",
            "severity": "mild",
            "reaction": "Test reaction",
            "status": "invalid_status"
        }

        response = client.post(
            "/api/v1/allergies/",
            json=invalid_status_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

        # Test invalid date format
        invalid_date_data = {
            "allergen": "Test Allergen",
            "severity": "mild",
            "reaction": "Test reaction",
            "onset_date": "invalid-date-format"
        }

        response = client.post(
            "/api/v1/allergies/",
            json=invalid_date_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422

    def test_allergy_severity_ordering(self, client: TestClient, user_with_patient, authenticated_headers):
        """Test that allergies are properly ordered by severity."""
        # Create allergies with different severities
        allergies = [
            {
                "allergen": "Mild Allergen",
                "severity": "mild",
                "reaction": "Mild reaction",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Life Threatening Allergen",
                "severity": "life-threatening",
                "reaction": "Anaphylaxis",
                "onset_date": "2023-01-15",
                "status": "active"
            },
            {
                "allergen": "Severe Allergen",
                "severity": "severe",
                "reaction": "Severe reaction",
                "onset_date": "2023-01-15",
                "status": "active"
            }
        ]

        for allergy_data in allergies:
            client.post(
                "/api/v1/allergies/",
                json=allergy_data,
                headers=authenticated_headers
            )

        # Get allergies (should be ordered by severity: life-threatening, severe, moderate, mild)
        response = client.get("/api/v1/allergies/", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        
        # Filter to our test allergies and check ordering
        test_allergies = [
            allergy for allergy in data 
            if allergy["allergen"] in ["Mild Allergen", "Life Threatening Allergen", "Severe Allergen"]
        ]
        
        # Should be ordered by severity (most severe first)
        assert len(test_allergies) == 3
        severities = [allergy["severity"] for allergy in test_allergies]
        
        # Check that life-threatening comes before severe, and severe comes before mild
        life_threatening_idx = next(i for i, s in enumerate(severities) if s == "life-threatening")
        severe_idx = next(i for i, s in enumerate(severities) if s == "severe")
        mild_idx = next(i for i, s in enumerate(severities) if s == "mild")
        
        assert life_threatening_idx < severe_idx < mild_idx