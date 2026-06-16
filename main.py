import os
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.models import TaskCreate, SessionResponse, TaskBreakdownResponse
from api.db_manager import DatabaseManager
from api.gemini_client import GeminiClient

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waitfree")

app = FastAPI(
    title="WaitFree API",
    description="Backend API for ADHD Waiting Mode Task Breaker",
    version="1.0.0"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate managers
db_manager = DatabaseManager()
gemini_client = GeminiClient()

@app.post("/api/sessions", response_model=SessionResponse, status_code=201)
async def create_session(payload: TaskCreate):
    """
    Decomposes a new task using Gemini and caches the session and steps in SQLite.
    """
    logger.info(f"API Request: Create session for task '{payload.task_name}'")
    task_name = payload.task_name.strip()
    if not task_name:
        raise HTTPException(status_code=400, detail="Task name cannot be empty.")

    # Call Gemini to break down the task
    try:
        breakdown = gemini_client.decompose_task(task_name, payload.duration_minutes)
    except Exception as e:
        logger.error(f"Failed to decompose task: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating subtasks. Please try again.")

    # Store in SQLite database
    try:
        session_id = db_manager.create_session(
            task_name=task_name,
            duration_minutes=payload.duration_minutes,
            steps=breakdown["steps"]
        )
    except Exception as e:
        logger.error(f"Failed to save session to DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving session database records.")

    # Fetch and return the fully populated session
    session = db_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Created session could not be retrieved.")
    return session

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int):
    """
    Retrieves a session and its steps by ID.
    """
    logger.info(f"API Request: Get session {session_id}")
    session = db_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session

@app.put("/api/steps/{step_id}")
async def update_step_status(step_id: int, completed: bool = Query(..., description="Completed status of the step")):
    """
    Updates the completed status of a specific subtask step.
    If all steps in the session are completed, the session is marked as completed.
    """
    logger.info(f"API Request: Update step {step_id} to completed={completed}")
    success = db_manager.update_step_status(step_id, completed)
    if not success:
        raise HTTPException(status_code=404, detail="Step not found.")
    return {"success": True, "step_id": step_id, "completed": completed}

@app.get("/api/sessions")
async def list_sessions(limit: int = Query(20, ge=1, le=100)):
    """
    Lists recent sessions with summary completion details.
    """
    logger.info(f"API Request: List sessions (limit={limit})")
    return db_manager.get_all_sessions(limit)

@app.get("/api/stats")
async def get_stats():
    """
    Gets user statistics (completed sessions, total steps, daily streaks).
    """
    logger.info("API Request: Get user stats")
    return db_manager.get_user_stats()

# Mount frontend files
static_dir = os.path.join(os.path.dirname(__file__), "static")

@app.get("/")
def read_root():
    return RedirectResponse(url="/index.html")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logger.warning(f"Static directory not found at {static_dir}")
