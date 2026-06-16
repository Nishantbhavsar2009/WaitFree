import pytest
from fastapi.testclient import TestClient
from main import app, gemini_client, db_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    """
    Auto-use fixture to set up a test database and clean it up after tests.
    """
    # Use a temporary test database file
    test_db_path = "test_waitfree.db"
    monkeypatch.setattr(db_manager, "db_path", test_db_path)
    # Re-initialize DB tables in test DB
    db_manager._init_db()
    
    yield
    
    # Clean up test database file
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

import os

def test_home_redirect():
    """
    Verify that GET / redirects to index.html.
    """
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/index.html"

def test_create_session(monkeypatch):
    """
    Verify creating a new task session correctly calls the mock decomposition 
    and saves records in the SQLite database.
    """
    # Mock decompose_task method on the gemini_client instance
    mock_steps = [
        {"title": "Open laptop", "estimated_seconds": 60, "explanation": "Get ready."},
        {"title": "Open editor", "estimated_seconds": 60, "explanation": "Ready to write."}
    ]
    monkeypatch.setattr(
        gemini_client, 
        "decompose_task", 
        lambda task, duration: {"original_task": task, "steps": mock_steps}
    )

    payload = {"task_name": "Write code", "duration_minutes": 15}
    response = client.post("/api/sessions", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["task_name"] == "Write code"
    assert data["duration_minutes"] == 15
    assert len(data["steps"]) == 2
    assert data["steps"][0]["title"] == "Open laptop"
    assert data["steps"][0]["completed"] is False

def test_update_step_status(monkeypatch):
    """
    Verify that updating a step status updates the SQLite database correctly.
    """
    # Create a session first in SQLite
    steps = [
        {"title": "Fold one shirt", "estimated_seconds": 60, "explanation": "First shirt."}
    ]
    session_id = db_manager.create_session("Fold clothes", 10, steps)
    
    # Retrieve the session to find the auto-assigned step ID
    session = db_manager.get_session(session_id)
    step_id = session["steps"][0]["id"]
    
    # Mark step as completed
    response = client.put(f"/api/steps/{step_id}?completed=true")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Retrieve session again and verify both step and session are marked completed
    updated_session = db_manager.get_session(session_id)
    assert updated_session["steps"][0]["completed"] is True
    assert updated_session["completed"] is True

def test_get_stats_and_sessions(monkeypatch):
    """
    Verify retrieving stats and listing sessions.
    """
    # Empty stats first
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_sessions_completed"] == 0
    
    # Empty list
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 0
