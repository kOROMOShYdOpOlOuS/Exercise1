from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client():
    return TestClient(app_module.app, follow_redirects=False)


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client, activities):
    # Arrange
    path = "/activities"
    expected_activities = activities

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_student_to_activity(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.post(path, params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.post(path, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_student_already_signed_up(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.post(path, params=params)

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_unregister_removes_student_from_activity(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.delete(path, params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.delete(path, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_student(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"
    path = f"/activities/{activity_name}/signup"
    params = {"email": email}

    # Act
    response = client.delete(path, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
