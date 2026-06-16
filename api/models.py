from pydantic import BaseModel, Field
from typing import List, Optional

class TaskCreate(BaseModel):
    task_name: str = Field(..., description="The main daunting task the user wants to start.")
    duration_minutes: Optional[int] = Field(None, description="Optional time available before the user's next event/appointment.")

class SubtaskStep(BaseModel):
    title: str = Field(..., description="A concrete, action-oriented step that takes less than 2 minutes.")
    estimated_seconds: int = Field(..., description="Estimated time for this step in seconds. Must be <= 120.")
    explanation: str = Field(..., description="A short, clear instruction or tip to reduce starting friction.")

class TaskBreakdownResponse(BaseModel):
    original_task: str
    steps: List[SubtaskStep]

class SubtaskStepResponse(BaseModel):
    id: int
    title: str = Field(..., description="A concrete, action-oriented step that takes less than 2 minutes.")
    estimated_seconds: int = Field(..., description="Estimated time for this step in seconds. Must be <= 120.")
    explanation: str = Field(..., description="A short, clear instruction or tip to reduce starting friction.")
    position: int
    completed: bool

class SessionResponse(BaseModel):
    id: int
    task_name: str
    created_at: str
    duration_minutes: Optional[int]
    completed: bool
    steps: List[SubtaskStepResponse]

