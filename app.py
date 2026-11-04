"""Streamlit C# interview coach with task planning and email reminders."""

import os
from datetime import date, datetime, time, timedelta

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from tutor_core import (
    add_task,
    due_tasks,
    init_db,
    list_tasks,
    mark_task_complete,
    mark_task_reminded,
    send_task_reminder,
)


load_dotenv()
init_db()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
COACH_INSTRUCTIONS = """You are an expert C# and .NET interview coach.
Teach accurately and clearly, adapting the depth to the learner's experience.
Use idiomatic modern C# examples. Explain trade-offs and relevant time/space complexity.
When practicing, ask one focused question at a time, wait for the learner's answer,
then give supportive, specific feedback with strengths, corrections, and a follow-up.
Do not reveal a full solution before the learner has had a chance to try unless they ask.
Cover C# language features, object-oriented design, LINQ, async/await, collections,
garbage collection, .NET runtime, APIs, testing, system design, and behavioral interviews.
"""


def get_smtp_settings():
    """Read SMTP credentials from the local environment without displaying them."""
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "sender": os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")).strip(),
    }


def stream_tutor_reply(client, model, messages, errors):
    """Stream generated tutor text and preserve API errors for the UI."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            text = chunk.choices[0].delta.content
            if text:
                yield text
    except Exception as error:
        errors.append(error)


st.set_page_config(page_title="C# Interview Coach", page_icon=":material/school:", layout="wide")
st.session_state.setdefault("messages", [])

st.title("C# Interview Coach")
st.caption("Practice with an AI tutor. Plan your preparation and stay on top of what’s due.")

with st.sidebar:
    st.subheader("Tutor settings")
    api_key_input = st.text_input(
        "OpenAI API key",
        value="",
        type="password",
        help="Or set OPENAI_API_KEY in your local .env file.",
    )
    api_key = api_key_input or os.getenv("OPENAI_API_KEY", "")
    model_name = st.text_input("Model", value=DEFAULT_MODEL).strip()
    experience = st.selectbox("Your experience", ["Junior", "Mid-level", "Senior"])
    target_role = st.text_input("Target role", value="C# / .NET Developer")

    st.divider()
    st.subheader("Email reminders")
    smtp = get_smtp_settings()
    email_ready = all(smtp.values())
    if email_ready:
        st.success("SMTP is configured")
    else:
        st.info("Add SMTP settings to `.env` to send task reminders by email.")
    st.caption("In-app due alerts work without email setup.")

tasks = list_tasks()
now = datetime.now().replace(microsecond=0)
pending_tasks = [task for task in tasks if not task["completed"]]
overdue_tasks = [
    task for task in pending_tasks if datetime.fromisoformat(task["due_at"]) < now
]
upcoming_tasks = [
    task
    for task in pending_tasks
    if now <= datetime.fromisoformat(task["due_at"]) <= now + timedelta(hours=24)
]

if overdue_tasks:
    st.error(
        f"You have {len(overdue_tasks)} overdue preparation task(s). Review your plan below."
    )
if upcoming_tasks:
    st.warning(f"{len(upcoming_tasks)} preparation task(s) are due in the next 24 hours.")

metrics = st.columns(3)
metrics[0].metric("Pending tasks", len(pending_tasks))
metrics[1].metric("Due soon", len(upcoming_tasks))
metrics[2].metric("Completed", sum(1 for task in tasks if task["completed"]))

if email_ready and (overdue_tasks or upcoming_tasks):
    if st.button("Send due email reminders", icon=":material/mail:"):
        candidates = due_tasks(now, hours=24)
        sent = 0
        failures = []
        for task in candidates:
            if not task["email"]:
                continue
            try:
                send_task_reminder(task, smtp)
                mark_task_reminded(task["id"])
                sent += 1
            except Exception as error:
                failures.append(f"{task['title']}: {error}")
        if sent:
            st.success(f"Sent {sent} reminder email(s).")
        if failures:
            st.error("Some reminders could not be sent: " + "; ".join(failures))
        if not sent and not failures:
            st.info("No due tasks with a reminder email address were found.")

tutor_tab, plan_tab = st.tabs(["Tutor chat", "Preparation plan"])

with tutor_tab:
    if not st.session_state.messages:
        st.markdown("#### Choose a starting point")
        suggestions = [
            "Quiz me on C# async and await",
            "Explain value types vs reference types",
            "Give me a .NET system design question",
        ]
        suggestion_cols = st.columns(len(suggestions))
        for column, suggestion in zip(suggestion_cols, suggestions):
            if column.button(suggestion, key=f"suggest_{suggestion}", width="stretch"):
                st.session_state.pending_prompt = suggestion
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask a C# interview question or start a practice round...")
    if st.session_state.get("pending_prompt"):
        prompt = st.session_state.pop("pending_prompt")

    if prompt:
        if not api_key:
            st.warning("Add your OpenAI API key in the sidebar or in `.env` to start the tutor.")
        elif not model_name:
            st.warning("Enter a model name in the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            plan_context = "\n".join(
                f"- {task['title']} (due {task['due_at']})" for task in pending_tasks[:8]
            ) or "No pending preparation tasks."
            system_message = (
                f"{COACH_INSTRUCTIONS}\nLearner level: {experience}. "
                f"Target role: {target_role or 'C# / .NET Developer'}.\n"
                f"Their pending prep tasks:\n{plan_context}"
            )
            api_messages = [{"role": "system", "content": system_message}]
            api_messages.extend(st.session_state.messages)

            errors = []
            with st.chat_message("assistant"):
                answer = st.write_stream(
                    stream_tutor_reply(OpenAI(api_key=api_key), model_name, api_messages, errors)
                )
            if errors:
                st.error(f"The AI request failed: {errors[0]}")
            elif answer:
                st.session_state.messages.append({"role": "assistant", "content": answer})

with plan_tab:
    st.subheader("Build your preparation plan")
    with st.form("add_prep_task", clear_on_submit=True):
        title = st.text_input("Task", placeholder="Review async/await and Task<T>")
        task_type = st.selectbox(
            "Training type",
            ["C# concept", "Coding practice", "Mock interview", "System design", "Behavioral"],
        )
        details = st.text_area("Notes", placeholder="What do you want to practice?")
        due_date_col, due_time_col = st.columns(2)
        due_date = due_date_col.date_input("Due date", value=date.today() + timedelta(days=1))
        due_time = due_time_col.time_input("Due time", value=time(18, 0))
        reminder_email = st.text_input("Reminder email", placeholder="you@example.com")
        submitted = st.form_submit_button("Add task", type="primary")

    if submitted:
        if not title.strip():
            st.warning("Enter a task title.")
        else:
            due_at = datetime.combine(due_date, due_time)
            add_task(
                title=title.strip(),
                task_type=task_type,
                details=details.strip(),
                due_at=due_at,
                email=reminder_email.strip(),
            )
            st.success("Preparation task added.")
            st.rerun()

    st.subheader("Your tasks")
    if not tasks:
        st.info("Your plan is empty. Add a task above to get started.")
    else:
        for task in tasks:
            due_at = datetime.fromisoformat(task["due_at"])
            with st.container(border=True):
                title_col, due_col, action_col = st.columns([3, 2, 1])
                title_col.markdown(f"**{task['title']}**")
                title_col.caption(f"{task['task_type']} · {task['details'] or 'No notes'}")
                due_col.write(due_at.strftime("%b %d, %Y at %I:%M %p"))
                due_col.caption("Completed" if task["completed"] else "Pending")
                if not task["completed"] and action_col.button(
                    "Complete", key=f"complete_{task['id']}", icon=":material/check:"
                ):
                    mark_task_complete(task["id"])
                    st.rerun()

st.caption("In-app alerts appear when you open or interact with the app. Email reminders are sent only when you choose the send button.")