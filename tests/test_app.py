import copy
import pytest

from fastapi.testclient import TestClient

from src import app as application


@application.app.get("/__ping_test_reset__")
def _ping_test_reset():
    # helper route to ensure the app is reachable in tests; not used directly
    return {"ok": True}


@pytest.fixture(autouse=True)
def restore_activities():
    """Snapshot the in-memory activities and restore after each test to
    keep tests isolated.
    """
    original = copy.deepcopy(application.activities)
    yield
    application.activities.clear()
    application.activities.update(original)


def test_get_activities():
    client = TestClient(application.app)

    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect some known activity keys
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    client = TestClient(application.app)
    activity = "Chess Club"
    email = "test.student@mergington.edu"

    # Ensure email not present initially
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Verify participant added
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email in resp.json()[activity]["participants"]

    # Duplicate signup should fail
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400

    # Unregister
    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify removal
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]


def test_unregister_nonexistent_returns_404():
    client = TestClient(application.app)
    activity = "Chess Club"
    email = "ghost@mergington.edu"

    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 404
