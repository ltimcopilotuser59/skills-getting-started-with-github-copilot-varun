"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original participants
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    # Restore original participants after test
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Should return all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Soccer Team" in data

    def test_activity_has_required_fields(self, client):
        """Each activity should have description, schedule, max_participants, and participants"""
        response = client.get("/activities")
        data = response.json()
        
        for name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Should successfully sign up a new student"""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Signing up should add the student to the participants list"""
        email = "teststudent@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Soccer Team"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Should return 404 for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self, client):
        """Should return 400 if student is already signed up"""
        # First signup
        client.post("/activities/Soccer Team/signup?email=duplicate@mergington.edu")
        # Second signup with same email
        response = client.post(
            "/activities/Soccer Team/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Should successfully unregister a student"""
        # First sign up
        email = "tounregister@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_from_list(self, client):
        """Unregistering should remove the student from participants list"""
        email = "removetest@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Soccer Team"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Should return 404 for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client):
        """Should return 400 if student is not signed up"""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client):
        """Root should redirect to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
