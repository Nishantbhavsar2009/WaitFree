import pytest
from fastapi.testclient import TestClient
import os
import sqlite3

# Import our FastAPI app and database module
import sys
sys.path.append(os.path.dirname(__file__))

from main import app
import database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes a clean, separate test database for each run."""
    # Temporarily override database path to test database
    orig_db_path = database.DB_PATH
    database.DB_PATH = os.path.join(os.path.dirname(__file__), "test_waitfree.db")
    
    # Initialize schema
    database.init_db()
    
    yield
    
    # Clean up test database file
    if os.path.exists(database.DB_PATH):
        try:
            os.remove(database.DB_PATH)
        except Exception:
            pass
            
    database.DB_PATH = orig_db_path

def test_api_create_task():
    # Test task creation with standard inputs
    response = client.post("/api/tasks", json={
        "title": "Study CBSE Physics practical experiments",
        "minutes_left": 30
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Study CBSE Physics practical experiments"
    assert data["minutes_left"] == 30
    assert "subtasks" in data
    assert len(data["subtasks"]) > 0
    
    # Every subtask must be action-oriented and under 120 seconds
    for subtask in data["subtasks"]:
        assert "title" in subtask
        assert subtask["duration_seconds"] <= 120
        assert subtask["completed"] == 0

def test_api_invalid_task_creation():
    # Empty title error check
    response = client.post("/api/tasks", json={
        "title": "",
        "minutes_left": 30
    })
    assert response.status_code == 400
    
    # Invalid minutes left check
    response = client.post("/api/tasks", json={
        "title": "Do homework",
        "minutes_left": 0
    })
    assert response.status_code == 400

def test_api_update_subtask_status():
    # Create a task first
    create_response = client.post("/api/tasks", json={
        "title": "Code website layout",
        "minutes_left": 45
    })
    task_data = create_response.json()
    subtask = task_data["subtasks"][0]
    subtask_id = subtask["id"]
    
    # Patch subtask completion status
    update_response = client.patch(f"/api/subtasks/{subtask_id}", json={
        "completed": True
    })
    assert update_response.status_code == 200
    assert update_response.json() == {"status": "success"}
    
    # Verify DB update in task detail
    detail_response = client.get(f"/api/tasks/{task_data['id']}")
    assert detail_response.status_code == 200
    updated_subtasks = detail_response.json()["subtasks"]
    assert updated_subtasks[0]["completed"] == 1

def test_api_stats():
    # Stats endpoint retrieval check
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "completed_tasks" in stats
    assert "completed_subtasks" in stats
    assert "streak" in stats
    assert "total_xp" in stats
    assert "level" in stats

def test_api_subtask_crud_operations():
    # 1. Create a task
    create_response = client.post("/api/tasks", json={
        "title": "Clean practical lab notes",
        "minutes_left": 15,
        "coaching_vibe": "ZEN"
    })
    assert create_response.status_code == 200
    task_data = create_response.json()
    task_id = task_data["id"]
    subtasks = task_data["subtasks"]
    assert len(subtasks) > 0
    
    # 2. Add a new subtask
    add_response = client.post(f"/api/tasks/{task_id}/subtasks", json={
        "title": "Zen deep breath session",
        "duration_seconds": 45
    })
    assert add_response.status_code == 200
    new_subtask_id = add_response.json()["id"]
    
    # Verify subtask added
    detail_response = client.get(f"/api/tasks/{task_id}")
    updated_subtasks = detail_response.json()["subtasks"]
    assert any(sub["id"] == new_subtask_id for sub in updated_subtasks)
    
    # 3. Edit the new subtask
    edit_response = client.patch(f"/api/subtasks/{new_subtask_id}/content", json={
        "title": "Mindful clean wrapup",
        "duration_seconds": 90
    })
    assert edit_response.status_code == 200
    
    # Verify changes
    detail_response2 = client.get(f"/api/tasks/{task_id}")
    updated_subtasks2 = detail_response2.json()["subtasks"]
    target_sub = next(sub for sub in updated_subtasks2 if sub["id"] == new_subtask_id)
    assert target_sub["title"] == "Mindful clean wrapup"
    assert target_sub["duration_seconds"] == 90
    
    # 4. Delete the subtask
    delete_response = client.delete(f"/api/subtasks/{new_subtask_id}")
    assert delete_response.status_code == 200
    
    # Verify deleted
    detail_response3 = client.get(f"/api/tasks/{task_id}")
    updated_subtasks3 = detail_response3.json()["subtasks"]
    assert not any(sub["id"] == new_subtask_id for sub in updated_subtasks3)

