"""
Test emergency contact API endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.patient import patient as patient_crud
from app.schemas.patient import PatientCreate


class TestEmergencyContactAPI:
    """Test emergency contact API endpoints."""

    @pytest.fixture
    def test_patient_for_contacts(self, db_session: Session, test_user):
        """Create test patient for emergency contact tests."""
        patient_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            birth_date="1990-01-01",
            gender="M",
            address="123 Main St"
        )
        return patient_crud.create_for_user(
            db_session, user_id=test_user.id, patient_data=patient_data
        )

    def test_create_emergency_contact(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test creating a new emergency contact."""
        patient = test_patient_for_contacts
        
        contact_data = {
            "name": "Jane Doe",
            "relationship": "spouse",
            "phone_number": "555-123-4567",
            "secondary_phone": "555-987-6543",
            "email": "jane.doe@example.com",
            "is_primary": True,
            "is_active": True,
            "address": "123 Main St, Anytown, USA",
            "notes": "Available 24/7"
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["relationship"] == "spouse"
        assert data["phone_number"] == "555-123-4567"
        assert data["email"] == "jane.doe@example.com"
        assert data["is_primary"] is True
        assert data["patient_id"] == patient.id

    def test_get_emergency_contacts_by_patient(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test getting emergency contacts for a patient."""
        patient = test_patient_for_contacts
        
        # Create test contacts
        contacts_data = [
            {
                "name": "Primary Contact",
                "relationship": "spouse",
                "phone_number": "555-111-1111",
                "is_primary": True
            },
            {
                "name": "Secondary Contact",
                "relationship": "parent",
                "phone_number": "555-222-2222",
                "is_primary": False
            }
        ]
        
        created_contacts = []
        for contact_data in contacts_data:
            response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
            assert response.status_code == 201
            created_contacts.append(response.json())
        
        # Get contacts for patient
        response = authenticated_client.get(f"/api/v1/emergency-contacts/patient/{patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify contacts (should be ordered with primary first)
        assert data[0]["is_primary"] is True
        assert data[0]["name"] == "Primary Contact"

    def test_get_primary_contact(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test getting primary emergency contact."""
        patient = test_patient_for_contacts
        
        # Create contacts
        contacts_data = [
            {
                "name": "Non-Primary Contact",
                "relationship": "friend",
                "phone_number": "555-111-1111",
                "is_primary": False
            },
            {
                "name": "Primary Contact",
                "relationship": "spouse",
                "phone_number": "555-222-2222",
                "is_primary": True
            }
        ]
        
        for contact_data in contacts_data:
            response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
            assert response.status_code == 201
        
        # Get primary contact
        response = authenticated_client.get(f"/api/v1/emergency-contacts/patient/{patient.id}/primary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Primary Contact"
        assert data["is_primary"] is True

    def test_update_emergency_contact(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test updating an emergency contact."""
        patient = test_patient_for_contacts
        
        # Create contact
        contact_data = {
            "name": "Original Name",
            "relationship": "friend",
            "phone_number": "555-111-1111",
            "email": "original@example.com"
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
        assert response.status_code == 201
        contact = response.json()
        
        # Update contact
        update_data = {
            "name": "Updated Name",
            "phone_number": "555-999-9999",
            "email": "updated@example.com",
            "is_primary": True
        }
        
        response = authenticated_client.put(f"/api/v1/emergency-contacts/{contact['id']}", json=update_data)
        
        assert response.status_code == 200
        updated_contact = response.json()
        assert updated_contact["name"] == "Updated Name"
        assert updated_contact["phone_number"] == "555-999-9999"
        assert updated_contact["email"] == "updated@example.com"
        assert updated_contact["is_primary"] is True
        assert updated_contact["relationship"] == "friend"  # Unchanged

    def test_set_primary_contact(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test setting a contact as primary."""
        patient = test_patient_for_contacts
        
        # Create two contacts
        contact1_data = {
            "name": "Contact 1",
            "relationship": "friend",
            "phone_number": "555-111-1111",
            "is_primary": True
        }
        
        contact2_data = {
            "name": "Contact 2",
            "relationship": "sibling",
            "phone_number": "555-222-2222",
            "is_primary": False
        }
        
        # Create first contact as primary
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact1_data)
        assert response.status_code == 201
        
        # Create second contact
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact2_data)
        assert response.status_code == 201
        contact2 = response.json()
        
        # Set contact2 as primary
        response = authenticated_client.put(f"/api/v1/emergency-contacts/{contact2['id']}/set-primary")
        
        assert response.status_code == 200
        
        # Verify contact2 is now primary
        response = authenticated_client.get(f"/api/v1/emergency-contacts/patient/{patient.id}/primary")
        assert response.status_code == 200
        primary_contact = response.json()
        assert primary_contact["id"] == contact2["id"]
        assert primary_contact["name"] == "Contact 2"

    def test_delete_emergency_contact(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test deleting an emergency contact."""
        patient = test_patient_for_contacts
        
        # Create contact
        contact_data = {
            "name": "Contact to Delete",
            "relationship": "neighbor",
            "phone_number": "555-777-8888"
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
        assert response.status_code == 201
        contact = response.json()
        
        # Delete contact
        response = authenticated_client.delete(f"/api/v1/emergency-contacts/{contact['id']}")
        
        assert response.status_code == 200
        
        # Verify contact is deleted
        response = authenticated_client.get(f"/api/v1/emergency-contacts/{contact['id']}")
        assert response.status_code == 404

    def test_get_active_contacts_only(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test getting only active emergency contacts."""
        patient = test_patient_for_contacts
        
        # Create active and inactive contacts
        contacts_data = [
            {
                "name": "Active Contact",
                "relationship": "spouse",
                "phone_number": "555-111-1111",
                "is_active": True
            },
            {
                "name": "Inactive Contact",
                "relationship": "friend",
                "phone_number": "555-222-2222",
                "is_active": False
            }
        ]
        
        for contact_data in contacts_data:
            response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
            assert response.status_code == 201
        
        # Get active contacts only
        response = authenticated_client.get(f"/api/v1/emergency-contacts/patient/{patient.id}?active_only=true")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Contact"
        assert data[0]["is_active"] is True

    def test_contact_validation_errors(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test emergency contact validation errors."""
        patient = test_patient_for_contacts
        
        # Test missing required fields
        invalid_contact = {
            "name": "Test Contact",
            # Missing relationship and phone_number (required)
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=invalid_contact)
        assert response.status_code == 422
        
        # Test invalid relationship
        invalid_relationship_contact = {
            "name": "Test Contact",
            "relationship": "invalid_relationship",
            "phone_number": "555-111-1111"
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=invalid_relationship_contact)
        assert response.status_code == 422
        
        # Test invalid phone number format
        invalid_phone_contact = {
            "name": "Test Contact",
            "relationship": "friend",
            "phone_number": "123"  # Too short
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=invalid_phone_contact)
        assert response.status_code == 422

    def test_email_validation(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test email validation and normalization."""
        patient = test_patient_for_contacts
        
        # Test valid email (should be normalized to lowercase)
        contact_data = {
            "name": "Email Test Contact",
            "relationship": "friend",
            "phone_number": "555-111-1111",
            "email": "Test.Email@Example.COM"
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test.email@example.com"  # Should be normalized

    def test_unauthorized_access(self, client: TestClient, test_patient_for_contacts):
        """Test unauthorized access to emergency contact endpoints."""
        patient = test_patient_for_contacts
        
        # Test without authentication
        response = client.get(f"/api/v1/emergency-contacts/patient/{patient.id}")
        assert response.status_code == 401
        
        # Test creating contact without auth
        contact_data = {
            "name": "Test Contact",
            "relationship": "friend",
            "phone_number": "555-111-1111"
        }
        
        response = client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact_data)
        assert response.status_code == 401

    def test_multiple_primary_contact_handling(self, authenticated_client: TestClient, test_patient_for_contacts):
        """Test that only one primary contact can exist per patient."""
        patient = test_patient_for_contacts
        
        # Create first primary contact
        contact1_data = {
            "name": "First Primary",
            "relationship": "spouse",
            "phone_number": "555-111-1111",
            "is_primary": True
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact1_data)
        assert response.status_code == 201
        
        # Create second primary contact (should unset the first)
        contact2_data = {
            "name": "Second Primary",
            "relationship": "parent",
            "phone_number": "555-222-2222",
            "is_primary": True
        }
        
        response = authenticated_client.post(f"/api/v1/emergency-contacts/patient/{patient.id}", json=contact2_data)
        assert response.status_code == 201
        
        # Verify only the second contact is primary
        response = authenticated_client.get(f"/api/v1/emergency-contacts/patient/{patient.id}/primary")
        assert response.status_code == 200
        primary_contact = response.json()
        assert primary_contact["name"] == "Second Primary"