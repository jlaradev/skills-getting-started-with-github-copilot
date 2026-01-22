"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original state
    original_activities = {
        activity: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for activity, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity, details in original_activities.items():
        activities[activity]["participants"] = details["participants"].copy()


def test_root_redirects_to_static(client):
    """Test that root path redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data
    assert "Soccer Club" in data
    assert "Programming Class" in data
    
    # Check structure of an activity
    basketball = data["Basketball Team"]
    assert "description" in basketball
    assert "schedule" in basketball
    assert "max_participants" in basketball
    assert "participants" in basketball


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    email = "test@mergington.edu"
    activity_name = "Basketball Team"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    assert activity_name in result["message"]
    
    # Verify participant was added
    assert email in activities[activity_name]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    email = "test@mergington.edu"
    activity_name = "Nonexistent Activity"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response.status_code == 404
    
    result = response.json()
    assert "detail" in result
    assert "not found" in result["detail"].lower()


def test_signup_duplicate_participant(client):
    """Test signing up the same participant twice"""
    email = "duplicate@mergington.edu"
    activity_name = "Art Club"
    
    # First signup should succeed
    response1 = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert response2.status_code == 400
    
    result = response2.json()
    assert "detail" in result
    assert "already signed up" in result["detail"].lower()


def test_unregister_from_activity_success(client):
    """Test successfully unregistering from an activity"""
    email = "unregister@mergington.edu"
    activity_name = "Soccer Club"
    
    # First signup
    client.post(f"/activities/{activity_name}/signup?email={email}")
    assert email in activities[activity_name]["participants"]
    
    # Then unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert email in result["message"]
    assert activity_name in result["message"]
    
    # Verify participant was removed
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    email = "test@mergington.edu"
    activity_name = "Nonexistent Activity"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 404
    
    result = response.json()
    assert "detail" in result
    assert "not found" in result["detail"].lower()


def test_unregister_participant_not_signed_up(client):
    """Test unregistering a participant who is not signed up"""
    email = "notsignedup@mergington.edu"
    activity_name = "Drama Club"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert response.status_code == 400
    
    result = response.json()
    assert "detail" in result
    assert "not signed up" in result["detail"].lower()


def test_activity_max_participants_preserved(client):
    """Test that max_participants is correctly maintained"""
    response = client.get("/activities")
    data = response.json()
    
    for activity, details in data.items():
        assert details["max_participants"] > 0
        assert len(details["participants"]) <= details["max_participants"]


def test_existing_participants_in_chess_club(client):
    """Test that Chess Club has pre-existing participants"""
    response = client.get("/activities")
    data = response.json()
    
    chess_club = data["Chess Club"]
    assert len(chess_club["participants"]) == 2
    assert "michael@mergington.edu" in chess_club["participants"]
    assert "daniel@mergington.edu" in chess_club["participants"]


def test_existing_participants_in_programming_class(client):
    """Test that Programming Class has pre-existing participants"""
    response = client.get("/activities")
    data = response.json()
    
    programming = data["Programming Class"]
    assert len(programming["participants"]) == 2
    assert "emma@mergington.edu" in programming["participants"]
    assert "sophia@mergington.edu" in programming["participants"]


def test_signup_and_unregister_workflow(client):
    """Test complete workflow: signup, verify, unregister, verify"""
    email = "workflow@mergington.edu"
    activity_name = "Debate Team"
    
    # Get initial state
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Verify signup
    after_signup = client.get("/activities")
    after_signup_count = len(after_signup.json()[activity_name]["participants"])
    assert after_signup_count == initial_count + 1
    assert email in after_signup.json()[activity_name]["participants"]
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    
    # Verify unregister
    after_unregister = client.get("/activities")
    after_unregister_count = len(after_unregister.json()[activity_name]["participants"])
    assert after_unregister_count == initial_count
    assert email not in after_unregister.json()[activity_name]["participants"]
