import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "waitfree.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    duration_minutes INTEGER,
                    completed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)
            # Create steps table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    estimated_seconds INTEGER NOT NULL,
                    explanation TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    completed INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
            """)
            conn.commit()

    def create_session(self, task_name: str, duration_minutes: Optional[int], steps: List[Dict[str, Any]]) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (task_name, duration_minutes, completed, created_at) VALUES (?, ?, 0, ?);",
                (task_name, duration_minutes, created_at)
            )
            session_id = cursor.lastrowid
            
            for index, step in enumerate(steps):
                cursor.execute(
                    """
                    INSERT INTO steps (session_id, title, estimated_seconds, explanation, position, completed)
                    VALUES (?, ?, ?, ?, ?, 0);
                    """,
                    (session_id, step["title"], step["estimated_seconds"], step["explanation"], index)
                )
            conn.commit()
            return session_id

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?;", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                return None
            
            session = dict(session_row)
            session["completed"] = bool(session["completed"])
            
            cursor.execute("SELECT * FROM steps WHERE session_id = ? ORDER BY position ASC;", (session_id,))
            step_rows = cursor.fetchall()
            session["steps"] = [dict(row) for row in step_rows]
            for step in session["steps"]:
                step["completed"] = bool(step["completed"])
                
            return session

    def update_step_status(self, step_id: int, completed: bool) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE steps SET completed = ? WHERE id = ?;", (1 if completed else 0, step_id))
            if cursor.rowcount == 0:
                return False
                
            # Get session_id associated with this step to verify if all steps are completed
            cursor.execute("SELECT session_id FROM steps WHERE id = ?;", (step_id,))
            session_id = cursor.fetchone()["session_id"]
            
            # Check if all steps of this session are completed
            cursor.execute("SELECT COUNT(*) as uncompleted FROM steps WHERE session_id = ? AND completed = 0;", (session_id,))
            uncompleted_count = cursor.fetchone()["uncompleted"]
            
            # Update session status
            session_completed = 1 if uncompleted_count == 0 else 0
            cursor.execute("UPDATE sessions SET completed = ? WHERE id = ?;", (session_completed, session_id))
            conn.commit()
            return True

    def get_all_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?;", (limit,))
            session_rows = cursor.fetchall()
            
            sessions = []
            for row in session_rows:
                session = dict(row)
                session["completed"] = bool(session["completed"])
                # Fetch steps count
                cursor.execute("SELECT COUNT(*) as total, SUM(completed) as completed_count FROM steps WHERE session_id = ?;", (session["id"],))
                stats = cursor.fetchone()
                session["total_steps"] = stats["total"] or 0
                session["completed_steps"] = stats["completed_count"] or 0
                sessions.append(session)
            return sessions

    def get_user_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Total completed sessions
            cursor.execute("SELECT COUNT(*) as completed_count FROM sessions WHERE completed = 1;")
            completed_sessions = cursor.fetchone()["completed_count"]
            
            # Total completed micro-tasks
            cursor.execute("SELECT COUNT(*) as completed_count FROM steps WHERE completed = 1;")
            completed_steps = cursor.fetchone()["completed_count"]
            
            # Fetch all completion dates to calculate streaks
            cursor.execute("SELECT DISTINCT date(created_at) as completed_date FROM sessions WHERE completed = 1 ORDER BY completed_date DESC;")
            rows = cursor.fetchall()
            completed_dates = [row["completed_date"] for row in rows]
            
            # Calculate current streak
            current_streak = 0
            today = datetime.utcnow().date()
            
            # Format dates to date objects
            date_objs = []
            for date_str in completed_dates:
                try:
                    date_objs.append(datetime.strptime(date_str, "%Y-%m-%d").date())
                except ValueError:
                    pass
            
            # Check streak
            if date_objs:
                last_date = date_objs[0]
                if last_date == today or last_date == today - sqlite3.register_adapter(datetime, lambda d: d): # Check if today or yesterday
                    # Check how many consecutive days there are
                    current_streak = 1
                    prev_date = last_date
                    for date_obj in date_objs[1:]:
                        diff = (prev_date - date_obj).days
                        if diff == 1:
                            current_streak += 1
                            prev_date = date_obj
                        elif diff == 0:
                            continue
                        else:
                            break
            
            return {
                "total_sessions_completed": completed_sessions,
                "total_micro_tasks_completed": completed_steps,
                "current_streak": current_streak
            }
