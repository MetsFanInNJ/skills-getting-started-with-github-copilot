from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_seeded_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert activities["Chess Club"]["max_participants"] == 12
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    activity = "Soccer Team"
    email = "student@example.com"
    response = client.post(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in client.get("/activities").json()[activity]["participants"]


def test_signup_rejects_duplicate_participant(client):
    activity = "Soccer Team"
    email = "student@example.com"
    activity_path = quote(activity, safe="")
    client.post(f"/activities/{activity_path}/signup", params={"email": email})

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()[activity]["participants"].count(email) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    activity = "Chess Club"
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/participants/{quote(email, safe='')}"
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants/student%40example.com"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(client):
    activity = "Soccer Team"
    email = "student@example.com"
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/participants/{quote(email, safe='')}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"