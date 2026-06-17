import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

import database

app = FastAPI(title="WaitFree — ADHD Waiting Mode Task Breaker")

# Initialize SQLite database on startup
@app.on_event("startup")
def startup_db():
    database.init_db()

# Mount static folder
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve UI at root
@app.get("/", response_class=FileResponse)
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Pydantic schemas
class TaskCreate(BaseModel):
    title: str
    minutes_left: int

class SubTaskUpdate(BaseModel):
    completed: bool

# Local fallback task breaker
def get_local_fallback_steps(title: str, minutes_left: int) -> List[dict]:
    title_lower = title.lower()
    
    # Study / Academic tasks
    if any(k in title_lower for k in ["study", "read", "learn", "math", "phys", "chem", "history", "exam", "homework", "practical"]):
        steps = [
            {"title": "Stand up, stretch, and clear your workspace of phones or distractions", "duration_seconds": 60},
            {"title": "Open your book, document, or practical sheet to the exact page needed", "duration_seconds": 60},
            {"title": "Write down a single key concept or formula you want to cover first on a sticky note", "duration_seconds": 60},
            {"title": "Read exactly one paragraph or page (set a timer if it helps)", "duration_seconds": 120},
            {"title": "Summarize what you read in a single sentence or write one definition", "duration_seconds": 120},
            {"title": "Answer one single review question or complete one simple math line", "duration_seconds": 120}
        ]
    # Code / Programming / Project tasks
    elif any(k in title_lower for k in ["code", "write", "program", "build", "project", "git", "dev", "bug", "fix", "app"]):
        steps = [
            {"title": "Open your terminal or IDE (VS Code, etc.)", "duration_seconds": 45},
            {"title": "Open the specific file or directory where you need to work", "duration_seconds": 45},
            {"title": "Write a one-line comment describing the next function, bug fix, or line of code", "duration_seconds": 60},
            {"title": "Write exactly 3-5 lines of code for this function", "duration_seconds": 120},
            {"title": "Run the compiler, test suit, or check command to see if it executes", "duration_seconds": 90},
            {"title": "Run a git status to review your modifications", "duration_seconds": 60}
        ]
    # Cleaning / Chore tasks
    elif any(k in title_lower for k in ["clean", "wash", "tidy", "room", "house", "clothes", "laundry", "dishes", "organize"]):
        steps = [
            {"title": "Put on a fast, high-energy song to set the pacing", "duration_seconds": 60},
            {"title": "Put away exactly 3 visible items from your floor or desk", "duration_seconds": 90},
            {"title": "Wipe down your primary desk or table surface", "duration_seconds": 90},
            {"title": "Gather any stray laundry/clothes and throw them into the hamper", "duration_seconds": 120},
            {"title": "Take one plate or cup to the kitchen sink and rinse it", "duration_seconds": 90}
        ]
    # Default generic tasks
    else:
        steps = [
            {"title": "Take one slow, deep breath to center your focus", "duration_seconds": 30},
            {"title": "Open a blank text file or grab a physical piece of paper", "duration_seconds": 60},
            {"title": "Write down the absolute smallest action item for this task", "duration_seconds": 60},
            {"title": "Do that single item for exactly 90 seconds (don't worry about quality)", "duration_seconds": 90},
            {"title": "Take a 30-second break, cross off the item, and prepare for the next step", "duration_seconds": 60}
        ]
        
    # Filter steps to fit the available time budget
    available_seconds = minutes_left * 60
    total_dur = 0
    filtered_steps = []
    
    for step in steps:
        if total_dur + step["duration_seconds"] <= available_seconds:
            filtered_steps.append(step)
            total_dur += step["duration_seconds"]
            
    # Always guarantee at least 2 steps
    if not filtered_steps:
        filtered_steps = steps[:2]
        
    return filtered_steps

def break_task_into_steps(title: str, minutes_left: int) -> List[dict]:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are an expert ADHD coach specializing in overcoming task initiation friction (the 2-minute rule).
            The user wants to accomplish the following task: "{title}"
            But they are experiencing "waiting mode" paralysis before an event in {minutes_left} minutes.
            
            Break down the task into highly granular, low-friction subtasks.
            Constraints:
            1. Every subtask MUST take less than 120 seconds (2 minutes) to complete. Keep them extremely small, simple, and action-oriented.
            2. The total duration of all subtasks combined MUST NOT exceed {minutes_left} minutes.
            3. Provide exactly what is needed to get started immediately, step-by-step.
            
            Format your response strictly as JSON matching this schema:
            {{
              "subtasks": [
                {{
                  "title": "Clear action-oriented step (e.g. 'Open chemistry textbook to page 45')",
                  "duration_seconds": 120
                }}
              ]
            }}
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "subtasks": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.OBJECT,
                                    properties={
                                        "title": types.Schema(type=types.Type.STRING),
                                        "duration_seconds": types.Schema(type=types.Type.INTEGER)
                                    },
                                    required=["title", "duration_seconds"]
                                )
                            )
                        },
                        required=["subtasks"]
                    )
                )
            )
            data = json.loads(response.text)
            if "subtasks" in data and isinstance(data["subtasks"], list) and len(data["subtasks"]) > 0:
                return data["subtasks"]
        except Exception as e:
            print(f"Error calling Gemini: {e}. Falling back to local rules.")
            
    # Fallback
    return get_local_fallback_steps(title, minutes_left)

@app.post("/api/tasks")
def api_create_task(data: TaskCreate):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    if data.minutes_left <= 0:
        raise HTTPException(status_code=400, detail="Minutes left must be greater than zero")
        
    subtasks = break_task_into_steps(data.title, data.minutes_left)
    task_id = database.create_task(data.title, data.minutes_left, subtasks)
    
    return database.get_task(task_id)

@app.get("/api/tasks")
def api_get_tasks():
    return database.get_all_tasks()

@app.get("/api/tasks/{task_id}")
def api_get_task_details(task_id: int):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/api/subtasks/{subtask_id}")
def api_update_subtask(subtask_id: int, data: SubTaskUpdate):
    success = database.update_subtask_status(subtask_id, data.completed)
    if not success:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return {"status": "success"}

@app.get("/api/stats")
def api_get_stats():
    return database.get_daily_stats()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
