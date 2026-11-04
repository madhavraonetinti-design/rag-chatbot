"""Persistence and email helpers for the C# interview coach."""

import smtplib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("data") / "tutor_tasks.sqlite3"


@contextmanager
def connect(database_path=DATABASE_PATH):
    """Yield a SQLite connection and always close its file handle."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db(database_path=DATABASE_PATH):
    """Create the preparation task table if it does not exist."""
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS prep_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                task_type TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                due_at TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_reminded_at TEXT
            )
            """
        )


def add_task(title, task_type, details, due_at, email, database_path=DATABASE_PATH):
    """Save a new preparation task with its local due time."""
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO prep_tasks (title, task_type, details, due_at, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, task_type, details, due_at.isoformat(), email, datetime.now().isoformat()),
        )
        return cursor.lastrowid


def list_tasks(database_path=DATABASE_PATH):
    """Return all tasks ordered by incomplete status and due date."""
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM prep_tasks ORDER BY completed ASC, due_at ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def due_tasks(now=None, hours=24, database_path=DATABASE_PATH):
    """Return pending tasks due within the next window, including overdue tasks."""
    now = now or datetime.now()
    cutoff = (now + timedelta(hours=hours)).isoformat()
    cooldown = (now - timedelta(hours=24)).isoformat()
    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM prep_tasks
            WHERE completed = 0 AND due_at <= ?
              AND (last_reminded_at IS NULL OR last_reminded_at <= ?)
            ORDER BY due_at ASC
            """,
            (cutoff, cooldown),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_task_complete(task_id, database_path=DATABASE_PATH):
    """Mark a preparation task complete."""
    with connect(database_path) as connection:
        connection.execute("UPDATE prep_tasks SET completed = 1 WHERE id = ?", (task_id,))


def mark_task_reminded(task_id, database_path=DATABASE_PATH):
    """Record a successfully sent reminder to avoid repeated emails."""
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE prep_tasks SET last_reminded_at = ? WHERE id = ?",
            (datetime.now().isoformat(), task_id),
        )


def send_task_reminder(task, settings):
    """Send one task reminder using SMTP SSL or STARTTLS."""
    required = ("host", "port", "username", "password", "sender")
    if not all(settings.get(key) for key in required):
        raise ValueError("SMTP settings are incomplete. Check your local .env file.")
    if not task.get("email"):
        raise ValueError("This task has no reminder email address.")

    due_at = datetime.fromisoformat(task["due_at"])
    message = EmailMessage()
    message["Subject"] = f"C# interview prep reminder: {task['title']}"
    message["From"] = settings["sender"]
    message["To"] = task["email"]
    message.set_content(
        f"A reminder for your C# interview preparation task:\n\n"
        f"{task['title']} ({task['task_type']})\n"
        f"Due: {due_at.strftime('%A, %B %d at %I:%M %p')}\n\n"
        f"{task.get('details') or 'Open your C# Interview Coach to review your plan.'}\n"
    )

    if int(settings["port"]) == 465:
        with smtplib.SMTP_SSL(settings["host"], 465, timeout=20) as server:
            server.login(settings["username"], settings["password"])
            server.send_message(message)
    else:
        with smtplib.SMTP(settings["host"], int(settings["port"]), timeout=20) as server:
            server.starttls()
            server.login(settings["username"], settings["password"])
            server.send_message(message)