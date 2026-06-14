"""
Test suite for the High School Management System API

Tests cover:
- Root redirect functionality
- Activity listing
- Student signup and duplicate signup handling
- Participant removal
"""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


_initial_activities = None


@pytest.fixture(autouse=True)
def restore_activities_state():
    """Restore the in-memory activity state before each test."""
    global _initial_activities

    if _initial_activities is None:
        _initial_activities = deepcopy(activities)

    activities.clear()
    activities.update(deepcopy(_initial_activities))

    yield


@pytest.fixture
def client():
    """Provide a TestClient instance for the FastAPI app."""
    return TestClient(app)


def test_root_redirect(client):
    # Arrange
    # No additional setup required.

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    # Arrange
    # The restore_activities_state fixture has already reset the activities.

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_for_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count + 1


def test_duplicate_signup(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1


def test_remove_nonexistent_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
