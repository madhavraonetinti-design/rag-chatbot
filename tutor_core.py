"""Persistence and email helpers for the C# interview coach."""

import smtplib
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
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
    """Create local tables for tasks, roadmap progress, quizzes, activity, and daily lessons."""
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS roadmap_progress (
                topic TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'Not started',
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_assignments (
                assignment_date TEXT PRIMARY KEY,
                day_index INTEGER NOT NULL,
                topic TEXT NOT NULL,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                objective TEXT NOT NULL,
                exercise TEXT NOT NULL,
                deliverable TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                reminder_sent_at TEXT
            )
            """
        )


def get_daily_assignment(
    assignment_date,
    curriculum,
    database_path=DATABASE_PATH,
    start_date=date(2026, 11, 4),
):
    """Get or generate the stable curriculum assignment for a calendar day."""
    if not curriculum:
        raise ValueError("The daily curriculum is empty.")
    day_index = (assignment_date - start_date).days % len(curriculum)
    lesson = curriculum[day_index]
    date_text = assignment_date.isoformat()
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO daily_assignments (
                assignment_date, day_index, topic, title, difficulty, minutes,
                objective, exercise, deliverable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_text,
                day_index,
                lesson["topic"],
                lesson["title"],
                lesson["difficulty"],
                lesson["minutes"],
                lesson["objective"],
                lesson["exercise"],
                lesson["deliverable"],
            ),
        )
        row = connection.execute(
            "SELECT * FROM daily_assignments WHERE assignment_date = ?", (date_text,)
        ).fetchone()
    return dict(row)


def list_daily_assignments(days=7, through=None, database_path=DATABASE_PATH):
    """Return daily lessons already generated in the requested date range."""
    through = through or date.today()
    start = (through - timedelta(days=days - 1)).isoformat()
    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM daily_assignments
            WHERE assignment_date >= ? AND assignment_date <= ?
            ORDER BY assignment_date DESC
            """,
            (start, through.isoformat()),
        ).fetchall()
    return [dict(row) for row in rows]


def complete_daily_assignment(assignment_date, database_path=DATABASE_PATH):
    """Mark today's assignment complete and record its learning activity."""
    date_text = assignment_date.isoformat()
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT title, completed FROM daily_assignments WHERE assignment_date = ?",
            (date_text,),
        ).fetchone()
        if row and not row["completed"]:
            connection.execute(
                "UPDATE daily_assignments SET completed = 1 WHERE assignment_date = ?",
                (date_text,),
            )
            connection.execute(
                "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
                ("Daily training", f"Completed {row['title']}", datetime.now().isoformat()),
            )


def mark_daily_assignment_reminded(assignment_date, database_path=DATABASE_PATH):
    """Record successful delivery of the daily Gmail assignment notification."""
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE daily_assignments SET reminder_sent_at = ? WHERE assignment_date = ?",
            (datetime.now().isoformat(), assignment_date.isoformat()),
        )


def send_daily_assignment_email(assignment, recipient, settings, pending_tasks=None):
    """Send the daily lesson and due task reminders to the configured learner."""
    required = ("host", "port", "username", "password", "sender")
    if not all(settings.get(key) for key in required):
        raise ValueError("SMTP settings are incomplete. Check your local .env file.")
    if not recipient or "@" not in recipient:
        raise ValueError("Set DAILY_TRAINING_EMAIL to a valid recipient address.")

    message = EmailMessage()
    message["Subject"] = f"Your .NET task for {assignment['assignment_date']}: {assignment['title']}"
    message["From"] = settings["sender"]
    message["To"] = recipient
    task_section = ""
    if pending_tasks:
        task_lines = []
        for task in pending_tasks:
            due_at = datetime.fromisoformat(task["due_at"])
            state = "OVERDUE" if due_at < datetime.now() else "DUE SOON"
            task_lines.append(
                f"- {task['title']} ({task['task_type']}) — {state}; "
                f"due {due_at.strftime('%b %d at %I:%M %p')}"
            )
        task_section = "\n\nPENDING TASKS\n" + "\n".join(task_lines)

    message.set_content(
        f"Your daily C# and .NET training assignment\n\n"
        f"{assignment['title']} ({assignment['difficulty']}, about {assignment['minutes']} minutes)\n"
        f"Topic: {assignment['topic']}\n\n"
        f"TODAY'S OBJECTIVE\n{assignment['objective']}\n\n"
        f"PRACTICE\n{assignment['exercise']}\n\n"
        f"DELIVERABLE\n{assignment['deliverable']}\n\n"
        "Open your C# Interview Studio to mark this lesson complete and ask the tutor for help."
        f"{task_section}\n"
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


def get_roadmap_progress(database_path=DATABASE_PATH):
    """Return saved roadmap statuses keyed by topic name."""
    with connect(database_path) as connection:
        rows = connection.execute("SELECT topic, status FROM roadmap_progress").fetchall()
    return {row["topic"]: row["status"] for row in rows}


def set_roadmap_status(topic, status, database_path=DATABASE_PATH):
    """Save a roadmap status and record newly completed topics as activity."""
    if status not in {"Not started", "In progress", "Completed"}:
        raise ValueError("Invalid roadmap status.")
    with connect(database_path) as connection:
        current = connection.execute(
            "SELECT status FROM roadmap_progress WHERE topic = ?", (topic,)
        ).fetchone()
        previous_status = current["status"] if current else "Not started"
        connection.execute(
            """
            INSERT INTO roadmap_progress (topic, status, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(topic) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at
            """,
            (topic, status, datetime.now().isoformat()),
        )
        if status == "Completed" and previous_status != "Completed":
            connection.execute(
                "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
                ("Roadmap", f"Completed {topic}", datetime.now().isoformat()),
            )


def save_quiz_attempt(level, score, total, database_path=DATABASE_PATH):
    """Persist a quiz result and add it to learning activity."""
    created_at = datetime.now().isoformat()
    with connect(database_path) as connection:
        connection.execute(
            "INSERT INTO quiz_attempts (level, score, total, created_at) VALUES (?, ?, ?, ?)",
            (level, score, total, created_at),
        )
        connection.execute(
            "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
            ("Interview prep", f"Completed a {level} quiz ({score}/{total})", created_at),
        )


def get_quiz_stats(database_path=DATABASE_PATH):
    """Return aggregate quiz score and number of attempts."""
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(SUM(score), 0) AS score, COALESCE(SUM(total), 0) AS total, COUNT(*) AS attempts FROM quiz_attempts"
        ).fetchone()
    return dict(row)


def log_activity(category, detail, database_path=DATABASE_PATH):
    """Record one completed learning action for dashboard analytics."""
    with connect(database_path) as connection:
        connection.execute(
            "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
            (category, detail, datetime.now().isoformat()),
        )


def get_activity(days=7, database_path=DATABASE_PATH):
    """Return activity entries from the last requested number of days."""
    start = (datetime.now() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT category, detail, created_at FROM learning_activity WHERE created_at >= ? ORDER BY created_at DESC",
            (start.isoformat(),),
        ).fetchall()
    return [dict(row) for row in rows]


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
        connection.execute(
            "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
            ("Learning plan", f"Added {title}", datetime.now().isoformat()),
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
        row = connection.execute(
            "SELECT title, completed FROM prep_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row and not row["completed"]:
            connection.execute("UPDATE prep_tasks SET completed = 1 WHERE id = ?", (task_id,))
            connection.execute(
                "INSERT INTO learning_activity (category, detail, created_at) VALUES (?, ?, ?)",
                ("Learning plan", f"Completed {row['title']}", datetime.now().isoformat()),
            )


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