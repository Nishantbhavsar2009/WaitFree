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
    coaching_vibe: Optional[str] = "MILITARY"

class SubTaskUpdate(BaseModel):
    completed: bool

class SubTaskContentUpdate(BaseModel):
    title: str
    duration_seconds: int

class SubTaskCreate(BaseModel):
    title: str
    duration_seconds: int

def format_step_by_vibe(step_title: str, vibe: str) -> str:
    vibe = vibe.upper()
    if vibe == "MILITARY":
        cleaned = step_title.replace("Stand up, stretch, and clear", "INITIALIZE: Clear") \
                            .replace("Open your", "DECODE: Open") \
                            .replace("Open the", "DECODE: Open") \
                            .replace("Write down a", "EXECUTE: Write") \
                            .replace("Write a", "EXECUTE: Write") \
                            .replace("Write exactly", "EXECUTE: Write") \
                            .replace("Read exactly", "EXECUTE: Read") \
                            .replace("Summarize what", "CONFIRM: Summarize") \
                            .replace("Answer one", "EXECUTE: Solve") \
                            .replace("Put on a", "INITIALIZE: Set") \
                            .replace("Put away", "EXECUTE: Clean") \
                            .replace("Wipe down", "EXECUTE: Clear") \
                            .replace("Gather any", "EXECUTE: Tidy") \
                            .replace("Take one", "EXECUTE: Move") \
                            .replace("Take a", "STANDBY: Take")
        if not any(prefix in cleaned for prefix in ["INITIALIZE", "DECODE", "EXECUTE", "CONFIRM", "STANDBY"]):
            cleaned = f"EXECUTE: {cleaned}"
        return cleaned
    elif vibe == "EMPATHETIC":
        softened = step_title.replace("Stand up, stretch, and clear", "Stretch gently, and clear a peaceful workspace") \
                             .replace("Open your", "Gently open your") \
                             .replace("Open the", "Find and open the") \
                             .replace("Write down a", "Just scribble a single") \
                             .replace("Write a", "Jot down a quick") \
                             .replace("Write exactly", "Write just") \
                             .replace("Read exactly", "Read just") \
                             .replace("Summarize what", "Celebrate by writing a tiny summary of what") \
                             .replace("Answer one", "Try answering just one") \
                             .replace("Put on a", "Play a nice, happy") \
                             .replace("Put away", "Quietly put away") \
                             .replace("Wipe down", "Gently wipe down") \
                             .replace("Gather any", "Collect a few") \
                             .replace("Take one", "Comfortably take one") \
                             .replace("Take a", "Enjoy a nice")
        return f"{softened} 🌟"
    elif vibe == "ZEN":
        zenified = step_title.replace("Stand up, stretch, and clear", "Mindfully stand, breathe, and clear space") \
                             .replace("Open your", "With full presence, open your") \
                             .replace("Open the", "Quietly open the") \
                             .replace("Write down a", "Breathe in; write down one") \
                             .replace("Write a", "Inhale; write one simple") \
                             .replace("Write exactly", "With focus, write exactly") \
                             .replace("Read exactly", "Silently read exactly") \
                             .replace("Summarize what", "Exhale; capture a single summary of what") \
                             .replace("Answer one", "Exhale; solve one single") \
                             .replace("Put on a", "Tune into a calm") \
                             .replace("Put away", "Mindfully place") \
                             .replace("Wipe down", "Slowly wipe down") \
                             .replace("Gather any", "Gently gather") \
                             .replace("Take one", "Gently move one") \
                             .replace("Take a", "Deep inhale... release. Take a")
        return f"🧘 {zenified}"
    return step_title

# Local fallback task breaker
def get_local_fallback_steps(title: str, minutes_left: int, coaching_vibe: str = "MILITARY") -> List[dict]:
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
            formatted_title = format_step_by_vibe(step["title"], coaching_vibe)
            filtered_steps.append({"title": formatted_title, "duration_seconds": step["duration_seconds"]})
            total_dur += step["duration_seconds"]
            
    # Always guarantee at least 2 steps
    if not filtered_steps:
        for step in steps[:2]:
            formatted_title = format_step_by_vibe(step["title"], coaching_vibe)
            filtered_steps.append({"title": formatted_title, "duration_seconds": step["duration_seconds"]})
        
    return filtered_steps

def break_task_into_steps(title: str, minutes_left: int, coaching_vibe: str = "MILITARY") -> List[dict]:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from google import genai
            from google.genai import types
            
            vibe_instructions = {
                "MILITARY": "Act as a commanding Cadet Instructor. Formulate steps as strict, high-urgency, precise checklist commands (e.g. 'DECODE: Open textbook; EXECUTE: Read page 45; REPORT status'). Use prefix terms like 'DECODE', 'EXECUTE', 'INITIALIZE', 'CONFIRM', 'STANDBY'.",
                "EMPATHETIC": "Act as a warm, encouraging, low-friction coach. Frame steps very gently with positive reinforcement, emphasizing comfort, safety, and ease of starting (e.g. 'Gently open your book when you are ready', 'Take a deep breath and read just 3 lines, you got this!').",
                "ZEN": "Act as a calm, mindful Zen Master. Frame steps as meditative, slow, single-pointed acts of focus, prioritizing breathing, clearing mental clutter, and calm execution (e.g. 'Inhale deeply; quietly place the chemistry sheet on your desk; exhale; write one word')."
            }.get(coaching_vibe.upper(), "Act as a commanding Cadet Instructor.")
            
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are an expert ADHD coach specializing in overcoming task initiation friction (the 2-minute rule).
            The user wants to accomplish the following task: "{title}"
            But they are experiencing "waiting mode" paralysis before an event in {minutes_left} minutes.
            
            Coaching Vibe:
            {vibe_instructions}
            
            Break down the task into highly granular, low-friction subtasks matching this coaching vibe.
            Constraints:
            1. Every subtask MUST take less than 120 seconds (2 minutes) to complete. Keep them extremely small, simple, and action-oriented.
            2. The total duration of all subtasks combined MUST NOT exceed {minutes_left} minutes.
            3. Provide exactly what is needed to get started immediately, step-by-step.
            
            Format your response strictly as JSON matching this schema:
            {{
              "subtasks": [
                {{
                  "title": "Clear action-oriented step (formatted according to the requested coaching vibe)",
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
    return get_local_fallback_steps(title, minutes_left, coaching_vibe)

@app.post("/api/tasks")
def api_create_task(data: TaskCreate):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    if data.minutes_left <= 0:
        raise HTTPException(status_code=400, detail="Minutes left must be greater than zero")
        
    subtasks = break_task_into_steps(data.title, data.minutes_left, data.coaching_vibe or "MILITARY")
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

@app.patch("/api/subtasks/{subtask_id}/content")
def api_update_subtask_content(subtask_id: int, data: SubTaskContentUpdate):
    success = database.update_subtask_content(subtask_id, data.title, data.duration_seconds)
    if not success:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return {"status": "success"}

@app.delete("/api/subtasks/{subtask_id}")
def api_delete_subtask(subtask_id: int):
    success = database.delete_subtask(subtask_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return {"status": "success"}

@app.post("/api/tasks/{task_id}/subtasks")
def api_add_subtask(task_id: int, data: SubTaskCreate):
    subtask_id = database.add_subtask(task_id, data.title, data.duration_seconds)
    return {"status": "success", "id": subtask_id}

@app.get("/api/stats")
def api_get_stats():
    return database.get_daily_stats()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
