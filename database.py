import sqlite3
from datetime import datetime, date, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "waitfree.db")

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                minutes_left INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                completed INTEGER DEFAULT 0
            )
        """)
        
        # Create subtasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                duration_seconds INTEGER DEFAULT 120,
                completed INTEGER DEFAULT 0,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        """)
        
        # Create daily stats table for streak tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                completed_tasks INTEGER DEFAULT 0,
                completed_subtasks INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def create_task(title: str, minutes_left: int, subtasks_list: list):
    """Inserts a new task and its associated subtasks."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        
        # Insert main task
        cursor.execute(
            "INSERT INTO tasks (title, minutes_left, created_at) VALUES (?, ?, ?)",
            (title, minutes_left, created_at)
        )
        task_id = cursor.lastrowid
        
        # Insert subtasks
        for index, subtask in enumerate(subtasks_list):
            title_sub = subtask.get("title", "Quick Step")
            duration = subtask.get("duration_seconds", 120)
            cursor.execute(
                "INSERT INTO subtasks (task_id, title, duration_seconds, order_index) VALUES (?, ?, ?, ?)",
                (task_id, title_sub, duration, index)
            )
            
        conn.commit()
        return task_id

def get_task(task_id: int):
    """Retrieves a single task and all its subtasks."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Fetch task details
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task_row = cursor.fetchone()
        if not task_row:
            return None
            
        task = dict(task_row)
        
        # Fetch associated subtasks
        cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index ASC", (task_id,))
        subtasks = [dict(row) for row in cursor.fetchall()]
        task["subtasks"] = subtasks
        
        return task

def get_all_tasks(limit: int = 10):
    """Retrieves the most recent tasks."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index ASC", (task["id"],))
            task["subtasks"] = [dict(sub) for sub in cursor.fetchall()]
            tasks.append(task)
        return tasks

def update_subtask_status(subtask_id: int, completed: bool):
    """Updates the status of a subtask and adjusts daily stats."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        status_val = 1 if completed else 0
        
        # Get subtask details to check past state
        cursor.execute("SELECT task_id, completed FROM subtasks WHERE id = ?", (subtask_id,))
        subtask_row = cursor.fetchone()
        if not subtask_row:
            return False
            
        task_id, was_completed = subtask_row["task_id"], subtask_row["completed"]
        
        # Update subtask
        cursor.execute("UPDATE subtasks SET completed = ? WHERE id = ?", (status_val, subtask_id))
        
        # Update daily statistics if completing a new subtask
        if completed and not was_completed:
            increment_daily_stats(conn, completed_subtask=True)
        elif not completed and was_completed:
            decrement_daily_stats(conn, completed_subtask=True)
            
        # Check if all subtasks for this task are completed now
        cursor.execute("SELECT COUNT(*) as total FROM subtasks WHERE task_id = ?", (task_id,))
        total_subtasks = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as completed FROM subtasks WHERE task_id = ? AND completed = 1", (task_id,))
        completed_subtasks = cursor.fetchone()["completed"]
        
        # Update main task status
        is_task_completed = 1 if total_subtasks > 0 and total_subtasks == completed_subtasks else 0
        cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
        task_was_completed = cursor.fetchone()["completed"]
        
        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (is_task_completed, task_id))
        
        if is_task_completed and not task_was_completed:
            increment_daily_stats(conn, completed_task=True)
        elif not is_task_completed and task_was_completed:
            decrement_daily_stats(conn, completed_task=True)
            
        conn.commit()
        return True

def get_daily_stats(conn=None):
    """Returns today's statistics along with current streak details and cumulative progression."""
    today_str = date.today().isoformat()
    if conn:
        stats = _get_daily_stats_with_conn(conn, today_str, commit=False)
        _add_cumulative_stats(conn, stats)
        return stats
    with get_db_connection() as c:
        stats = _get_daily_stats_with_conn(c, today_str, commit=True)
        _add_cumulative_stats(c, stats)
        return stats

def _add_cumulative_stats(conn, stats):
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(completed_tasks) as total_tasks, SUM(completed_subtasks) as total_subtasks FROM daily_stats")
    row = cursor.fetchone()
    total_tasks = row["total_tasks"] or 0
    total_subtasks = row["total_subtasks"] or 0
    
    # Calculate XP (10 XP per subtask, 50 XP per full task)
    total_xp = (total_subtasks * 10) + (total_tasks * 50)
    
    # Gamification Levels
    if total_xp < 100:
        level = 1
        rank = "COGNITIVE_CADET"
        next_level_xp = 100
        prev_level_xp = 0
    elif total_xp < 300:
        level = 2
        rank = "INERTIA_BREAKER"
        next_level_xp = 300
        prev_level_xp = 100
    elif total_xp < 600:
        level = 3
        rank = "MOMENTUM_CAPTAIN"
        next_level_xp = 600
        prev_level_xp = 300
    elif total_xp < 1000:
        level = 4
        rank = "FOCUS_SENTINEL"
        next_level_xp = 1000
        prev_level_xp = 600
    else:
        level = 5
        rank = "ANTIGRAVITY_COMMANDER"
        next_level_xp = 1000
        prev_level_xp = 1000
        
    stats["total_completed_tasks"] = total_tasks
    stats["total_completed_subtasks"] = total_subtasks
    stats["total_xp"] = total_xp
    stats["level"] = level
    stats["rank"] = rank
    stats["next_level_xp"] = next_level_xp
    stats["prev_level_xp"] = prev_level_xp

def _get_daily_stats_with_conn(conn, today_str, commit=True):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (today_str,))
    row = cursor.fetchone()
    if row:
        return dict(row)
        
    # If no record exists for today, retrieve yesterday's streak to carry forward
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    cursor.execute("SELECT streak FROM daily_stats WHERE date = ?", (yesterday_str,))
    yesterday_row = cursor.fetchone()
    yesterday_streak = yesterday_row["streak"] if yesterday_row else 0
    
    # Initialize today's row
    cursor.execute(
        "INSERT OR IGNORE INTO daily_stats (date, completed_tasks, completed_subtasks, streak) VALUES (?, 0, 0, ?)",
        (today_str, yesterday_streak)
    )
    if commit:
        conn.commit()
    
    cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (today_str,))
    return dict(cursor.fetchone())

def increment_daily_stats(conn, completed_task=False, completed_subtask=False):
    """Internal helper to increment daily stats."""
    today_str = date.today().isoformat()
    cursor = conn.cursor()
    
    # Initialize today's row if not present
    get_daily_stats(conn)
    
    if completed_task:
        cursor.execute("UPDATE daily_stats SET completed_tasks = completed_tasks + 1, streak = CASE WHEN streak = 0 THEN 1 ELSE streak END WHERE date = ?", (today_str,))
    if completed_subtask:
        cursor.execute("UPDATE daily_stats SET completed_subtasks = completed_subtasks + 1 WHERE date = ?", (today_str,))

def decrement_daily_stats(conn, completed_task=False, completed_subtask=False):
    """Internal helper to decrement daily stats."""
    today_str = date.today().isoformat()
    cursor = conn.cursor()
    
    # Initialize today's row if not present
    get_daily_stats(conn)
    
    if completed_task:
        cursor.execute("UPDATE daily_stats SET completed_tasks = MAX(0, completed_tasks - 1) WHERE date = ?", (today_str,))
    if completed_subtask:
        cursor.execute("UPDATE daily_stats SET completed_subtasks = MAX(0, completed_subtasks - 1) WHERE date = ?", (today_str,))

def update_subtask_content(subtask_id: int, title: str, duration_seconds: int):
    """Updates the title and duration of a subtask."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE subtasks SET title = ?, duration_seconds = ? WHERE id = ?",
            (title, duration_seconds, subtask_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_subtask(subtask_id: int):
    """Deletes a subtask and adjusts task completion status if needed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Fetch task_id of subtask first
        cursor.execute("SELECT task_id, completed FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            return False
        task_id, was_completed = row["task_id"], row["completed"]
        
        # Delete the subtask
        cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
        
        # Decrement daily stats if the deleted subtask was completed
        if was_completed:
            decrement_daily_stats(conn, completed_subtask=True)
            
        # Re-check and update main task completion
        cursor.execute("SELECT COUNT(*) as total FROM subtasks WHERE task_id = ?", (task_id,))
        total_subtasks = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as completed FROM subtasks WHERE task_id = ? AND completed = 1", (task_id,))
        completed_subtasks = cursor.fetchone()["completed"]
        
        is_task_completed = 1 if total_subtasks > 0 and total_subtasks == completed_subtasks else 0
        cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
        task_was_completed = cursor.fetchone()["completed"]
        
        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (is_task_completed, task_id))
        
        if is_task_completed and not task_was_completed:
            increment_daily_stats(conn, completed_task=True)
        elif not is_task_completed and task_was_completed:
            decrement_daily_stats(conn, completed_task=True)
            
        conn.commit()
        return True

def add_subtask(task_id: int, title: str, duration_seconds: int):
    """Adds a new subtask to a task."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get the max order_index
        cursor.execute("SELECT MAX(order_index) as max_idx FROM subtasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        max_idx = row["max_idx"] if row["max_idx"] is not None else -1
        new_idx = max_idx + 1
        
        cursor.execute(
            "INSERT INTO subtasks (task_id, title, duration_seconds, order_index) VALUES (?, ?, ?, ?)",
            (task_id, title, duration_seconds, new_idx)
        )
        new_subtask_id = cursor.lastrowid
        
        # Update parent task to incomplete (since a new incomplete subtask is added)
        cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
        task_row = cursor.fetchone()
        if task_row and task_row["completed"] == 1:
            cursor.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
            decrement_daily_stats(conn, completed_task=True)
            
        conn.commit()
        return new_subtask_id


