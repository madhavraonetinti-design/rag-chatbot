"""APScheduler lifecycle and exactly-once daily Gmail lesson delivery."""

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from tutor_content import DAILY_CURRICULUM, DAILY_CURRICULUM_START_DATE
from tutor_core import (
    due_tasks,
    get_daily_assignment,
    mark_task_reminded,
    mark_daily_assignment_reminded,
    send_daily_assignment_email,
)


LOGGER = logging.getLogger(__name__)


def daily_email_configuration():
    """Return safe scheduling status and never include credential values."""
    recipient = os.getenv("DAILY_TRAINING_EMAIL", "").strip()
    smtp_ready = all(
        os.getenv(name, "").strip()
        for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD")
    )
    sender = os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")).strip()
    configured = smtp_ready and bool(recipient) and bool(sender)
    try:
        hour = int(os.getenv("DAILY_TRAINING_HOUR", "8"))
        minute = int(os.getenv("DAILY_TRAINING_MINUTE", "0"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        hour, minute = 8, 0
        configured = False
    timezone_name = os.getenv("DAILY_TRAINING_TIMEZONE", "local").strip() or "local"
    try:
        timezone = datetime.now().astimezone().tzinfo if timezone_name.lower() == "local" else ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        timezone = datetime.now().astimezone().tzinfo
        configured = False
    return {
        "configured": configured,
        "recipient": recipient,
        "hour": hour,
        "minute": minute,
        "timezone": timezone,
        "timezone_name": timezone_name,
    }


def send_daily_assignment_if_needed():
    """Send today's assignment only if it has not already been delivered."""
    config = daily_email_configuration()
    if not config["configured"]:
        LOGGER.info("Daily training email is not configured; skipping scheduled send.")
        return False

    today = datetime.now(config["timezone"]).date()
    assignment = get_daily_assignment(
        today, DAILY_CURRICULUM, start_date=DAILY_CURRICULUM_START_DATE
    )
    if assignment["reminder_sent_at"]:
        LOGGER.info("Daily assignment for %s was already emailed.", today.isoformat())
        return False

    smtp = {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "sender": os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")).strip(),
    }
    tasks = due_tasks(hours=24)
    send_daily_assignment_email(assignment, config["recipient"], smtp, pending_tasks=tasks)
    mark_daily_assignment_reminded(today)
    for task in tasks:
        mark_task_reminded(task["id"])
    LOGGER.info("Daily .NET assignment email sent for %s.", today.isoformat())
    return True


def start_daily_scheduler():
    """Start one process-wide daily scheduler when email settings are complete."""
    config = daily_email_configuration()
    if not config["configured"]:
        return None

    timezone = config["timezone"]
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(
        send_daily_assignment_if_needed,
        trigger=CronTrigger(hour=config["hour"], minute=config["minute"], timezone=timezone),
        id="daily-dotnet-assignment-email",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    # Deliver today's task when the app starts after the scheduled time. The DB
    # flag makes this safe across reloads and restarts.
    current_time = datetime.now(timezone)
    schedule_time = (config["hour"], config["minute"])
    if (current_time.hour, current_time.minute) >= schedule_time:
        try:
            send_daily_assignment_if_needed()
        except Exception:
            LOGGER.exception("Could not send today's .NET assignment email.")
    return scheduler