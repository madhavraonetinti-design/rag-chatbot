"""Premium Streamlit workspace for C# and .NET interview preparation."""

import os
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from code_runner import run_csharp_solution
from daily_scheduler import daily_email_configuration, start_daily_scheduler
from tutor_content import (
    CODING_CHALLENGES,
    DAILY_CURRICULUM,
    DAILY_CURRICULUM_START_DATE,
    QUESTIONS,
    ROADMAP,
)
from tutor_core import (
    add_task,
    complete_daily_assignment,
    due_tasks,
    get_daily_assignment,
    get_activity,
    get_quiz_stats,
    get_roadmap_progress,
    init_db,
    list_daily_assignments,
    list_tasks,
    log_activity,
    mark_task_complete,
    mark_task_reminded,
    mark_daily_assignment_reminded,
    save_quiz_attempt,
    send_task_reminder,
    send_daily_assignment_email,
    set_roadmap_status,
)


st.set_page_config(page_title="C# Interview Coach", page_icon=":material/school:", layout="wide")
load_dotenv()
init_db()


@st.cache_resource
def get_daily_scheduler():
    """Keep one APScheduler instance alive across Streamlit reruns."""
    return start_daily_scheduler()


daily_scheduler = get_daily_scheduler()
daily_email_config = daily_email_configuration()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
NAV_ITEMS = [
    ("Dashboard", ":material/dashboard:"),
    ("AI Chat", ":material/forum:"),
    ("Daily Training", ":material/today:"),
    ("Learning Roadmap", ":material/route:"),
    ("Interview Questions", ":material/quiz:"),
    ("Coding Practice", ":material/code:"),
    ("Mock Interviews", ":material/record_voice_over:"),
    ("Progress Analytics", ":material/monitoring:"),
    ("Settings", ":material/settings:"),
]
NAV_LABELS = {f"{icon}  {name}": name for name, icon in NAV_ITEMS}
NAV_BY_NAME = {name: f"{icon}  {name}" for name, icon in NAV_ITEMS}
COACH_INSTRUCTIONS = """You are an expert C# and .NET interview coach.
Teach accurately and clearly, adapting explanations to the learner's experience.
Use idiomatic modern C# code and explain trade-offs and relevant complexity.
During practice, ask one focused question at a time. Let the learner answer before
revealing a solution unless they explicitly ask for one. Give kind, specific feedback,
correct misconceptions, and offer a useful follow-up. Cover C#, OOP, LINQ, async/await,
collections, garbage collection, .NET, ASP.NET Core, APIs, testing, system design,
coding interviews, and behavioral interviews.
"""
HR_QUESTIONS = [
    "Tell me about a challenging technical problem you solved.",
    "Describe a time you disagreed with a teammate about an implementation.",
    "How do you handle a production issue under time pressure?",
    "Tell me about a mistake you made and what you learned from it.",
    "How do you explain a technical trade-off to a non-technical stakeholder?",
]


def get_smtp_settings():
    """Read private SMTP configuration from the local environment."""
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "sender": os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME", "")).strip(),
    }


def get_training_date():
    """Return the assignment date in the configured notification timezone."""
    return datetime.now(daily_email_config["timezone"]).date()


def stream_tutor_reply(client, model, messages, errors):
    """Stream tutor text from the Google AI Studio Gemini API."""
    try:
        system_instruction = next(
            (message["content"] for message in messages if message["role"] == "system"),
            None,
        )
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
            if message["role"] != "system"
        ]
        response = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as error:
        errors.append(error)


def set_navigation(page):
    """Switch navigation from a page action before the next Streamlit rerun."""
    st.session_state.nav_choice = NAV_BY_NAME[page]


def start_hr_practice(question):
    """Open a mock interview with the selected behavioral question queued."""
    st.session_state.nav_choice = NAV_BY_NAME["Mock Interviews"]
    st.session_state["pending_prompt_Mock interview"] = (
        f"Conduct a behavioral mock interview. Ask me this question first: {question}"
    )


def start_daily_training_chat(lesson):
    """Open AI Chat with today's assignment ready for coaching."""
    st.session_state.nav_choice = NAV_BY_NAME["AI Chat"]
    st.session_state["pending_prompt_AI tutor"] = (
        f"Coach me through today's .NET training assignment. Topic: {lesson['topic']}. "
        f"Task: {lesson['title']}. Objective: {lesson['objective']} "
        f"Exercise: {lesson['exercise']} Deliverable: {lesson['deliverable']} "
        "Ask me one focused question at a time and let me attempt the work before showing a solution."
    )


def get_conversation(mode):
    """Return the active mode-specific chat transcript."""
    sessions_key = f"sessions_{mode}"
    active_key = f"active_session_{mode}"
    if sessions_key not in st.session_state:
        session_id = f"{mode.lower().replace(' ', '-')}-1"
        st.session_state[sessions_key] = [{"id": session_id, "title": "New conversation", "messages": []}]
        st.session_state[active_key] = session_id
    sessions = st.session_state[sessions_key]
    active_id = st.session_state.get(active_key, sessions[0]["id"])
    active = next((session for session in sessions if session["id"] == active_id), sessions[0])
    st.session_state[active_key] = active["id"]
    return sessions, active


def record_tutor_message(mode, prompt, api_key, model_name, experience, target_role):
    """Request a tutor response, preserve the transcript, and track successful practice."""
    _, active = get_conversation(mode)
    active["messages"].append({"role": "user", "content": prompt})
    if active["title"] == "New conversation":
        active["title"] = prompt[:38] + ("…" if len(prompt) > 38 else "")

    plan = [task for task in list_tasks() if not task["completed"]]
    plan_context = "\n".join(f"- {task['title']} (due {task['due_at']})" for task in plan[:8])
    system_message = (
        f"{COACH_INSTRUCTIONS}\nLearner level: {experience}. Target role: {target_role}.\n"
        f"Their pending preparation tasks:\n{plan_context or 'No pending preparation tasks.'}"
    )
    messages = [{"role": "system", "content": system_message}, *active["messages"]]
    errors = []
    answer = st.write_stream(stream_tutor_reply(genai.Client(api_key=api_key), model_name, messages, errors))
    if errors:
        st.error(f"The AI request failed: {errors[0]}")
    elif answer:
        active["messages"].append({"role": "assistant", "content": answer})
        log_activity("Mock interview" if mode == "Mock interview" else "Tutor chat", prompt[:100])


def render_chat(mode, api_key, model_name, experience, target_role):
    """Render tutor chat or mock-interview chat with session history and suggestions."""
    sessions, active = get_conversation(mode)
    page_title = "Mock interview room" if mode == "Mock interview" else "AI tutor"
    st.markdown(f"<div class='eyebrow'>{mode.upper()}</div>", unsafe_allow_html=True)
    st.header(page_title)

    if mode == "Mock interview":
        st.caption("The tutor asks one interview question at a time and coaches your answer.")
    else:
        st.caption("Ask a C# question, explore a concept, or practice explaining your reasoning.")

    if len(sessions) > 1 or active["messages"]:
        with st.container(horizontal=True, vertical_alignment="bottom"):
            session_ids = [session["id"] for session in sessions]
            active_index = session_ids.index(active["id"])
            chosen_id = st.selectbox(
                "Chat history",
                session_ids,
                index=active_index,
                format_func=lambda item: next(s["title"] for s in sessions if s["id"] == item),
                key=f"history_picker_{mode}",
            )
            if chosen_id != active["id"]:
                st.session_state[f"active_session_{mode}"] = chosen_id
                st.rerun()
            if st.button("New chat", icon=":material/add:", key=f"new_chat_{mode}"):
                new_id = f"{mode.lower().replace(' ', '-')}-{datetime.now().timestamp()}"
                sessions.insert(0, {"id": new_id, "title": "New conversation", "messages": []})
                st.session_state[f"active_session_{mode}"] = new_id
                st.rerun()
            if active["messages"] and st.button(
                "Clear", icon=":material/delete:", key=f"clear_chat_{mode}"
            ):
                active["messages"] = []
                active["title"] = "New conversation"
                st.rerun()

    if not active["messages"]:
        if mode == "Mock interview":
            st.markdown(
                "<div class='empty-state'><div class='empty-icon'>:material/record_voice_over:</div>"
                "<h3>Your next interview starts here</h3><p>Choose a focus and the AI interviewer will take it from there.</p></div>",
                unsafe_allow_html=True,
            )
            suggestions = [
                "Start a junior C# technical interview",
                "Run a senior .NET system design interview",
                "Practice behavioral questions using STAR",
            ]
        else:
            st.markdown(
                "<div class='empty-state'><div class='empty-icon'>:material/auto_awesome:</div>"
                "<h3>Your C# learning copilot</h3><p>Ask a question or choose a prompt to begin.</p></div>",
                unsafe_allow_html=True,
            )
            suggestions = [
                "Explain OOP concepts in C#.",
                "What is async and await?",
                "Explain ASP.NET Core.",
                "Quiz me on C# fundamentals.",
                "Give me 10 .NET interview questions.",
            ]
        suggestion_cols = st.columns(min(3, len(suggestions)))
        for index, suggestion in enumerate(suggestions):
            col = suggestion_cols[index % len(suggestion_cols)]
            if col.button(suggestion, key=f"{mode}_suggestion_{index}", width="stretch"):
                st.session_state[f"pending_prompt_{mode}"] = suggestion
                st.rerun()

    for message in active["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Answer the interviewer..." if mode == "Mock interview" else "Ask your C# tutor...",
        key=f"chat_input_{mode}",
    )
    pending_prompt = st.session_state.pop(f"pending_prompt_{mode}", None)
    prompt = pending_prompt or prompt

    if prompt:
        if not api_key:
            st.warning("Add your Google AI Studio key in Settings or configure `GEMINI_API_KEY` in `.env`.")
        elif not model_name:
            st.warning("Set a model name in Settings.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                record_tutor_message(mode, prompt, api_key, model_name, experience, target_role)


def build_weekly_activity(entries):
    """Create a seven-day table from persisted activity events."""
    categories = ["Tutor chat", "Interview prep", "Coding practice", "Roadmap", "Learning plan", "Mock interview"]
    start_day = date.today() - timedelta(days=6)
    rows = []
    for offset in range(7):
        current_day = start_day + timedelta(days=offset)
        row = {"Day": current_day.strftime("%a")}
        for category in categories:
            row[category] = 0
        for entry in entries:
            created = datetime.fromisoformat(entry["created_at"])
            if created.date() == current_day:
                row[entry["category"]] = row.get(entry["category"], 0) + 1
        rows.append(row)
    return pd.DataFrame(rows).set_index("Day")


def render_task_planner(tasks, email_ready, smtp):
    """Render due alerts, reminders, creation form, and completion actions."""
    now = datetime.now().replace(microsecond=0)
    pending = [task for task in tasks if not task["completed"]]
    due_soon = [task for task in pending if datetime.fromisoformat(task["due_at"]) <= now + timedelta(hours=24)]
    overdue = [task for task in pending if datetime.fromisoformat(task["due_at"]) < now]

    if overdue:
        st.error(f"{len(overdue)} task(s) are overdue. Pick one and get back on track.", icon=":material/alarm:")
    if due_soon:
        st.warning(f"{len(due_soon)} task(s) are due in the next 24 hours.", icon=":material/schedule:")
    if email_ready and due_soon and st.button("Send due email reminders", icon=":material/mail:"):
        sent = 0
        failures = []
        for task in due_tasks(now, hours=24):
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
            st.info("No due tasks with a reminder email address are eligible for another reminder yet.")

    with st.expander("Plan a learning task", expanded=not tasks):
        with st.form("add_prep_task", clear_on_submit=True):
            title = st.text_input("Task", placeholder="Review async/await and Task<T>")
            task_type = st.selectbox(
                "Training type",
                ["C# concept", "Coding practice", "Mock interview", "System design", "Behavioral"],
            )
            details = st.text_input("Notes", placeholder="What do you want to practice?")
            date_col, time_col = st.columns(2)
            due_date = date_col.date_input("Due date", value=date.today() + timedelta(days=1))
            due_time = time_col.time_input("Due time", value=time(18, 0))
            email = st.text_input("Reminder email (optional)", placeholder="you@example.com")
            submitted = st.form_submit_button("Add task", type="primary", icon=":material/add_task:")
        if submitted:
            if not title.strip():
                st.warning("Enter a task title.")
            else:
                add_task(title.strip(), task_type, details.strip(), datetime.combine(due_date, due_time), email.strip())
                st.success("Task added to your plan.")
                st.rerun()

    if not tasks:
        st.markdown("<div class='quiet-note'>Your study plan is clear. Add a task above to set your next milestone.</div>", unsafe_allow_html=True)
        return

    for task in tasks:
        due_at = datetime.fromisoformat(task["due_at"])
        with st.container(border=True):
            title_col, due_col, action_col = st.columns([3, 2, 1], vertical_alignment="center")
            title_col.markdown(f"**{task['title']}**")
            title_col.caption(f"{task['task_type']} · {task['details'] or 'No notes'}")
            due_col.caption("Due")
            due_col.write(due_at.strftime("%b %d · %I:%M %p"))
            if task["completed"]:
                action_col.markdown(":green[:material/check_circle: Completed]")
            elif action_col.button("Complete", key=f"complete_task_{task['id']}", icon=":material/check:"):
                mark_task_complete(task["id"])
                st.rerun()


def render_dashboard(tasks, roadmap_progress, activity, quiz_stats, api_key, email_ready, smtp):
    """Render the welcome dashboard and real learning analytics."""
    st.markdown(
        "<div class='hero'><div><div class='eyebrow'>YOUR LEARNING STUDIO</div>"
        "<h1>Welcome Back! Ready to Master C# &amp; .NET?</h1>"
        "<p>Your personal AI-powered learning companion.</p></div>"
        "<div class='hero-mark'>C#<span>+</span></div></div>",
        unsafe_allow_html=True,
    )

    completed_tasks = sum(bool(task["completed"]) for task in tasks)
    completed_topics = sum(status == "Completed" for status in roadmap_progress.values())
    progress_total = len(tasks) + len(ROADMAP)
    progress_done = completed_tasks + completed_topics
    progress = int(progress_done / progress_total * 100) if progress_total else 0
    pending_tasks = [task for task in tasks if not task["completed"]]
    metrics = st.columns(4)
    metric_data = [
        ("Total learning tasks", len(tasks) + len(ROADMAP), ":material/format_list_bulleted:"),
        ("Completed tasks", completed_tasks + completed_topics, ":material/task_alt:"),
        ("Pending tasks", len(pending_tasks) + len(ROADMAP) - completed_topics, ":material/pending_actions:"),
        ("Learning progress", f"{progress}%", ":material/trending_up:"),
    ]
    for column, (label, value, icon) in zip(metrics, metric_data):
        with column.container(border=True):
            st.caption(f"{icon}  {label}")
            st.markdown(f"<div class='metric-value'>{value}</div>", unsafe_allow_html=True)

    activity_today = sum(
        datetime.fromisoformat(entry["created_at"]).date() == date.today() for entry in activity
    )
    if "daily_goal" not in st.session_state:
        st.session_state.daily_goal = 3

    progress_col, weekly_col = st.columns([1, 1.65])
    with progress_col.container(border=True):
        st.markdown("#### Daily learning goal")
        st.markdown(
            f"<div class='progress-ring' style='--progress:{progress}%'><div><strong>{progress}%</strong>"
            f"<span>overall</span></div></div>",
            unsafe_allow_html=True,
        )
        goal = st.slider("Daily goal · completed learning actions", 1, 10, key="daily_goal")
        st.progress(min(activity_today / goal, 1.0), text=f"{activity_today} of {goal} learning actions today")

    with weekly_col.container(border=True):
        st.markdown("#### Weekly learning activity")
        if activity:
            chart_data = build_weekly_activity(activity)
            st.bar_chart(chart_data, height=235, color=["#a78bfa", "#38bdf8", "#22d3ee", "#818cf8", "#c084fc", "#60a5fa"])
        else:
            st.markdown("<div class='chart-empty'>Complete a quiz, chat practice, roadmap milestone, or task to start your activity chart.</div>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Continue learning")
        next_topic = next(
            (item for item in ROADMAP if roadmap_progress.get(item[0], "Not started") != "Completed"),
            ROADMAP[0],
        )
        with st.container(border=True):
            st.markdown(f"<div class='eyebrow'>NEXT UP · {next_topic[1].upper()}</div>", unsafe_allow_html=True)
            st.subheader(next_topic[0])
            st.write(next_topic[2])
            if st.button("Open learning roadmap", type="primary", icon=":material/arrow_forward:", on_click=set_navigation, args=("Learning Roadmap",)):
                pass
        if not api_key:
            st.info("Add your AI API key in Settings to use the tutor chat.", icon=":material/key:")
        elif quiz_stats["attempts"]:
            st.caption(f"{quiz_stats['attempts']} quiz attempts saved · {quiz_stats['score']}/{quiz_stats['total']} correct overall")

    with right:
        st.markdown("#### Upcoming learning tasks")
        if pending_tasks:
            for task in sorted(pending_tasks, key=lambda item: item["due_at"])[:4]:
                with st.container(border=True):
                    st.markdown(f"**{task['title']}**")
                    st.caption(f"{task['task_type']} · {datetime.fromisoformat(task['due_at']).strftime('%a, %b %d')}")
                    if st.button("Mark complete", key=f"dashboard_complete_{task['id']}", icon=":material/check:"):
                        mark_task_complete(task["id"])
                        st.rerun()
        else:
            st.markdown("<div class='quiet-note'>No upcoming tasks. Add one to keep momentum.</div>", unsafe_allow_html=True)
        with st.expander("Recent activity"):
            if activity:
                for entry in activity[:5]:
                    created = datetime.fromisoformat(entry["created_at"])
                    st.markdown(f"**{entry['category']}** · {entry['detail']}")
                    st.caption(created.strftime("%b %d at %I:%M %p"))
            else:
                st.caption("Your completed learning actions will appear here.")

    st.markdown("#### Study plan")
    render_task_planner(tasks, email_ready, smtp)


def render_roadmap():
    """Render interactive, persistent learning pathway cards."""
    st.markdown("<div class='eyebrow'>STRUCTURED LEARNING</div>", unsafe_allow_html=True)
    st.title("Learning roadmap")
    st.caption("Move through a practical C# and .NET interview pathway at your own pace.")
    progress = get_roadmap_progress()
    done_count = sum(progress.get(topic, "Not started") == "Completed" for topic, _, _ in ROADMAP)
    st.progress(done_count / len(ROADMAP), text=f"{done_count} of {len(ROADMAP)} milestones complete")

    for start in range(0, len(ROADMAP), 2):
        columns = st.columns(2)
        for column, (topic, level, description) in zip(columns, ROADMAP[start : start + 2]):
            current_status = progress.get(topic, "Not started")
            with column.container(border=True, height="stretch"):
                st.markdown(f"<div class='eyebrow'>MILESTONE {start + 1 if topic == ROADMAP[start][0] else start + 2:02d} · {level.upper()}</div>", unsafe_allow_html=True)
                st.subheader(topic)
                st.write(description)
                selected_status = st.selectbox(
                    "Progress status",
                    ["Not started", "In progress", "Completed"],
                    index=["Not started", "In progress", "Completed"].index(current_status),
                    key=f"roadmap_status_{topic}",
                )
                if selected_status != current_status:
                    set_roadmap_status(topic, selected_status)
                    st.rerun()
                st.progress(1.0 if current_status == "Completed" else 0.5 if current_status == "In progress" else 0.0)


def render_interview_questions():
    """Render technical questions, HR prompts, and a scored multi-choice quiz."""
    st.markdown("<div class='eyebrow'>INTERVIEW PREPARATION</div>", unsafe_allow_html=True)
    st.title("Interview questions")
    prep_mode = st.segmented_control(
        "Practice format", ["Technical", "HR / behavioral", "Quick quiz"], default="Technical", key="interview_format"
    )
    level = st.selectbox("Difficulty level", ["Beginner", "Intermediate", "Advanced"], key="question_level")

    if prep_mode == "Technical":
        selected_questions = [item for item in QUESTIONS if item["level"] == level]
        for index, question in enumerate(selected_questions, start=1):
            with st.expander(f"{index:02d}  {question['question']}"):
                st.caption(f"{question['topic']} · {question['level']}")
                st.markdown(f"**Answer:** {question['options'][question['answer']]}")
                st.write(question["explanation"])
    elif prep_mode == "HR / behavioral":
        st.info("Structure a concise story with Situation, Task, Action, and Result (STAR). Focus on your specific contribution and what changed.")
        for index, question in enumerate(HR_QUESTIONS, start=1):
            with st.expander(f"{index:02d}  {question}"):
                st.markdown("**Practice prompt**")
                st.write("Answer in 1–2 minutes. Explain the context, your responsibility, the steps you personally took, and the measurable outcome.")
                if st.button("Practice with AI interviewer", key=f"hr_practice_{index}", on_click=start_hr_practice, args=(question,)):
                    pass
    else:
        quiz_questions = [item for item in QUESTIONS if item["level"] == level]
        state_key = f"quiz_{level.lower()}"
        st.session_state.setdefault(state_key, {"index": 0, "score": 0, "checked": False, "finished": False})
        quiz_state = st.session_state[state_key]
        if quiz_state["index"] >= len(quiz_questions):
            quiz_state["finished"] = True

        if quiz_state["finished"]:
            st.success(f"Quiz complete · {quiz_state['score']} of {len(quiz_questions)} correct")
            st.metric("Score", f"{round(quiz_state['score'] / len(quiz_questions) * 100)}%")
            if st.button("Try this level again", icon=":material/replay:"):
                st.session_state[state_key] = {"index": 0, "score": 0, "checked": False, "finished": False}
                st.rerun()
        else:
            question = quiz_questions[quiz_state["index"]]
            st.progress(quiz_state["index"] / len(quiz_questions), text=f"Question {quiz_state['index'] + 1} of {len(quiz_questions)}")
            st.markdown(f"### {question['question']}")
            choice = st.radio(
                "Choose your answer",
                question["options"],
                key=f"quiz_choice_{level}_{quiz_state['index']}",
                disabled=quiz_state["checked"],
            )
            if not quiz_state["checked"]:
                if st.button("Check answer", type="primary", icon=":material/check:"):
                    is_correct = question["options"].index(choice) == question["answer"]
                    quiz_state["score"] += int(is_correct)
                    quiz_state["checked"] = True
                    st.rerun()
            else:
                is_correct = question["options"].index(choice) == question["answer"]
                if is_correct:
                    st.success("Correct. Nice work.")
                else:
                    st.error(f"Not quite. The correct answer is: {question['options'][question['answer']]}")
                st.info(question["explanation"])
                if st.button("Next question", type="primary", icon=":material/arrow_forward:"):
                    quiz_state["index"] += 1
                    quiz_state["checked"] = False
                    if quiz_state["index"] >= len(quiz_questions):
                        quiz_state["finished"] = True
                        save_quiz_attempt(level, quiz_state["score"], len(quiz_questions))
                    st.rerun()


def render_coding_practice():
    """Render an editable C# challenge with actual local .NET compilation and tests."""
    st.markdown("<div class='eyebrow'>HANDS-ON PRACTICE</div>", unsafe_allow_html=True)
    st.title("Coding practice")
    challenge_name = st.selectbox("Challenge", list(CODING_CHALLENGES), key="coding_challenge")
    challenge = CODING_CHALLENGES[challenge_name]
    st.caption(f"{challenge['difficulty']} · C#")
    left, right = st.columns([1, 1.25])
    with left:
        st.markdown("#### Problem")
        st.write(challenge["description"])
        st.markdown("#### Test cases")
        st.code(challenge["harness"], language="csharp")
        st.caption("Run executes your code on this computer using the installed .NET SDK; it is not sandboxed.")
    with right:
        st.markdown("#### Your solution")
        code = st.text_area(
            "C# editor",
            value=challenge["starter"],
            height=390,
            max_chars=12000,
            key=f"solution_{challenge_name}",
        )
        with st.container(horizontal=True):
            run_clicked = st.button("Run tests", type="primary", icon=":material/play_arrow:")
            submit_clicked = st.button("Submit solution", icon=":material/task_alt:")
        if run_clicked or submit_clicked:
            with st.spinner("Compiling and running the C# test cases…"):
                result = run_csharp_solution(code, challenge["harness"])
            if not result["available"]:
                st.error(result["output"])
                st.markdown("Install the [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0), then restart VS Code.")
            elif result["passed"]:
                st.success(f"All {result['tests_passed']} test cases passed.")
                if submit_clicked:
                    log_activity("Coding practice", f"Submitted {challenge_name}")
                    st.toast("Solution submitted and added to your learning activity.")
            else:
                if result["tests_total"]:
                    st.warning(f"{result['tests_passed']} of {result['tests_total']} test cases passed.")
                else:
                    st.error("The solution did not build or run successfully.")
            st.code(result["output"], language="text")


def render_analytics(tasks, roadmap_progress, activity, quiz_stats):
    """Render analytics from persisted user actions and progress."""
    st.markdown("<div class='eyebrow'>YOUR MOMENTUM</div>", unsafe_allow_html=True)
    st.title("Progress analytics")
    task_completed = sum(bool(task["completed"]) for task in tasks)
    roadmap_completed = sum(status == "Completed" for status in roadmap_progress.values())
    columns = st.columns(4)
    columns[0].metric("Learning actions · 7 days", len(activity))
    columns[1].metric("Tasks completed", task_completed)
    columns[2].metric("Roadmap milestones", f"{roadmap_completed}/{len(ROADMAP)}")
    score = round(quiz_stats["score"] / quiz_stats["total"] * 100) if quiz_stats["total"] else 0
    columns[3].metric("Quiz accuracy", f"{score}%", help=f"{quiz_stats['score']} correct out of {quiz_stats['total']} answers")

    with st.container(border=True):
        st.markdown("#### Learning activity by day")
        if activity:
            st.bar_chart(build_weekly_activity(activity), height=320, color=["#a78bfa", "#38bdf8", "#22d3ee", "#818cf8", "#c084fc", "#60a5fa"])
        else:
            st.info("Complete a learning action to populate your weekly chart.")

    recent = get_activity(days=30)
    st.markdown("#### Recent activity")
    if recent:
        for entry in recent[:12]:
            when = datetime.fromisoformat(entry["created_at"])
            with st.container(border=True):
                activity_col, time_col = st.columns([3, 1])
                activity_col.markdown(f"**{entry['category']}** · {entry['detail']}")
                time_col.caption(when.strftime("%b %d · %I:%M %p"))
    else:
        st.caption("No recent activity yet.")


def render_daily_training(api_key):
    """Render today's deterministic .NET lesson and its completion/history."""
    st.markdown("<div class='eyebrow'>YOUR DAILY PRACTICE</div>", unsafe_allow_html=True)
    st.title("Daily .NET training")
    today = get_training_date()
    lesson = get_daily_assignment(
        today, DAILY_CURRICULUM, start_date=DAILY_CURRICULUM_START_DATE
    )
    completed_days = sum(item["completed"] for item in list_daily_assignments(days=30))
    left, right = st.columns([1.45, 0.8])

    with left.container(border=True):
        st.markdown(
            f"<div class='eyebrow'>{lesson['topic'].upper()} · {lesson['difficulty'].upper()} · {lesson['minutes']} MIN</div>",
            unsafe_allow_html=True,
        )
        st.header(lesson["title"])
        st.markdown("#### Today's objective")
        st.write(lesson["objective"])
        st.markdown("#### Practice task")
        st.write(lesson["exercise"])
        st.markdown("#### Deliverable")
        st.info(lesson["deliverable"])

        if lesson["completed"]:
            st.success("Today's training is complete. Come back tomorrow for the next lesson.")
        else:
            action_col, coach_col = st.columns(2)
            if action_col.button("Mark today's task complete", type="primary", icon=":material/task_alt:"):
                complete_daily_assignment(today)
                st.rerun()
            if coach_col.button(
                "Discuss with AI tutor",
                icon=":material/forum:",
                disabled=not api_key,
                on_click=start_daily_training_chat,
                args=(lesson,),
            ):
                st.rerun()
            if not api_key:
                st.caption("Set an AI API key in Settings to discuss this task with the tutor.")

    with right.container(border=True):
        st.markdown("#### Training streak")
        st.metric("Lessons completed · 30 days", completed_days)
        st.progress(1.0 if lesson["completed"] else 0.0, text="Today's lesson complete" if lesson["completed"] else "Today's lesson in progress")
        st.markdown("#### Daily email")
        if daily_email_config["configured"] and daily_scheduler:
            st.success("Scheduled Gmail delivery is active")
            st.caption(
                f"To {daily_email_config['recipient']} · "
                f"daily at {daily_email_config['hour']:02d}:{daily_email_config['minute']:02d} "
                f"({daily_email_config['timezone_name']})"
            )
        else:
            st.info("Configure Gmail SMTP and DAILY_TRAINING_EMAIL in `.env` to schedule a daily task email.")
        st.caption("The scheduler runs only while this Streamlit process is running.")

    history = list_daily_assignments(days=7)
    st.markdown("#### Recent daily assignments")
    for item in history:
        with st.container(border=True):
            day_col, lesson_col, status_col = st.columns([1, 3, 1])
            day_col.caption(item["assignment_date"])
            lesson_col.markdown(f"**{item['title']}** · {item['topic']}")
            status_col.markdown(":green[Complete]" if item["completed"] else "In progress")


def render_settings(api_key, model_name, experience, target_role, email_ready, smtp):
    """Render Gemini API health and local reminder configuration status."""
    st.markdown("<div class='eyebrow'>PREFERENCES & CONNECTIONS</div>", unsafe_allow_html=True)
    st.title("Settings")
    st.caption("Update the AI and learning preferences in the sidebar. Secrets stay in your local session or `.env` file.")
    with st.container(border=True):
        st.markdown("#### Google AI Studio")
        st.write(f"Model: `{model_name}`")
        st.write(f"Experience: {experience} · Target role: {target_role}")
        st.write("API key: configured" if api_key else "API key: not configured")
        if st.button("Test API connection", disabled=not api_key, icon=":material/bolt:"):
            try:
                model_info = genai.Client(api_key=api_key).models.get(model=model_name)
                st.success(f"Google AI Studio connection succeeded for `{model_info.name}`.")
            except Exception as error:
                st.error(f"API connection failed: {error}")
    with st.container(border=True):
        st.markdown("#### Email reminders")
        st.write("SMTP connection: configured" if email_ready else "SMTP connection: not configured")
        if email_ready:
            st.caption(f"Host `{smtp['host']}` · port {smtp['port']} · sender {smtp['sender']}")
        else:
            st.info("Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM in `.env` to send reminders.")
        st.markdown("#### Daily .NET assignment email")
        if daily_email_config["configured"] and daily_scheduler:
            st.success("Daily Gmail notifications are scheduled.")
            st.caption(
                f"Recipient: {daily_email_config['recipient']} · "
                f"Time: {daily_email_config['hour']:02d}:{daily_email_config['minute']:02d} "
                f"({daily_email_config['timezone_name']})"
            )
            if st.button("Send today's training email now", icon=":material/forward_to_inbox:"):
                try:
                    today = get_training_date()
                    today_lesson = get_daily_assignment(
                        today, DAILY_CURRICULUM, start_date=DAILY_CURRICULUM_START_DATE
                    )
                    pending_email_tasks = due_tasks(hours=24)
                    send_daily_assignment_email(
                        today_lesson,
                        daily_email_config["recipient"],
                        smtp,
                        pending_tasks=pending_email_tasks,
                    )
                    mark_daily_assignment_reminded(today)
                    for task in pending_email_tasks:
                        mark_task_reminded(task["id"])
                    st.success("Today's assignment email was sent.")
                except Exception as error:
                    st.error(f"The training email could not be sent: {error}")
        else:
            st.warning("Daily Gmail delivery is not active. Add the required settings to `.env` and restart the app.")
            st.caption("The schedule runs only while this Streamlit server is running.")
    with st.container(border=True):
        st.markdown("#### Local data")
        st.write("Task, roadmap, quiz, and activity records are stored in the local SQLite database.")
        st.caption("Chat transcripts remain in the current Streamlit browser session. They are sent to the configured AI API when you submit a message.")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#f4f2ff; --muted:#a5a2bd; --line:rgba(191,176,255,.15); --violet:#a78bfa; --blue:#60a5fa; --cyan:#67e8f9; }
    .stApp { background: radial-gradient(ellipse at 68% -12%, rgba(86,57,177,.22), transparent 36%), radial-gradient(ellipse at 0% 40%, rgba(28,92,155,.13), transparent 32%), #0b0a12; color:var(--ink); font-family:'DM Sans',sans-serif; }
    h1,h2,h3,h4 { font-family:'Space Grotesk','DM Sans',sans-serif !important; letter-spacing:0 !important; color:#f7f5ff; }
    h1 { font-size:2.35rem !important; line-height:1.13 !important; }
    .block-container { max-width:1420px; padding-top:2rem; padding-bottom:4rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#100e1b 0%,#0d0c15 100%); border-right:1px solid rgba(186,169,255,.12); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#b6b2cc; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.48rem .68rem; border-radius:10px; transition:background .18s ease, transform .18s ease; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(167,139,250,.1); transform:translateX(2px); }
    [data-testid="stVerticalBlockBorderWrapper"] { background:linear-gradient(145deg,rgba(26,23,40,.88),rgba(17,16,27,.91)); border-color:var(--line) !important; border-radius:16px !important; box-shadow:0 12px 32px rgba(0,0,0,.14); transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { border-color:rgba(167,139,250,.3) !important; box-shadow:0 15px 34px rgba(0,0,0,.22); }
    [data-testid="stMetric"] { background:transparent; }
    [data-testid="stMetricLabel"] { color:#aaa6c1 !important; }
    .metric-value { font-family:'Space Grotesk',sans-serif; font-size:2rem; line-height:1.15; font-weight:700; color:#f5f2ff; padding-top:.35rem; }
    .hero { display:flex; align-items:center; justify-content:space-between; gap:1.2rem; padding:2rem 2.2rem; margin:.4rem 0 1.5rem; border:1px solid rgba(190,174,255,.22); border-radius:20px; background:linear-gradient(110deg,rgba(76,49,143,.5),rgba(31,59,101,.36) 58%,rgba(16,18,29,.77)); box-shadow:0 18px 48px rgba(0,0,0,.25); overflow:hidden; position:relative; }
    .hero h1 { max-width:760px; margin:.45rem 0 .5rem; font-size:clamp(1.7rem,2.4vw,2.55rem) !important; }
    .hero p { color:#cbc6df; margin:0; font-size:1.02rem; }
    .hero-mark { flex:0 0 112px; width:112px; height:112px; display:grid; place-items:center; border-radius:30px; border:1px solid rgba(210,196,255,.32); background:linear-gradient(145deg,rgba(172,140,255,.28),rgba(70,166,255,.13)); box-shadow:inset 0 0 28px rgba(199,180,255,.12),0 0 38px rgba(130,100,255,.17); font:700 2.8rem 'Space Grotesk',sans-serif; color:#fff; transform:rotate(5deg); }
    .hero-mark span { color:#67e8f9; }
    .eyebrow { color:#a99bff; font-size:.72rem; font-weight:700; letter-spacing:.12em; margin-bottom:.45rem; }
    .progress-ring { width:150px; height:150px; margin:.55rem auto 1rem; border-radius:50%; display:grid; place-items:center; background:conic-gradient(#a78bfa var(--progress),#282438 0); position:relative; box-shadow:0 0 30px rgba(132,94,255,.13); animation:ring-in .8s ease-out; }
    @keyframes ring-in { from { transform:scale(.88) rotate(-35deg); opacity:.5; } to { transform:scale(1) rotate(0); opacity:1; } }
    .progress-ring:before { content:''; position:absolute; inset:10px; border-radius:50%; background:#151320; border:1px solid rgba(191,176,255,.13); }
    .progress-ring div { position:relative; display:grid; justify-items:center; }
    .progress-ring strong { font:700 1.8rem 'Space Grotesk',sans-serif; }
    .progress-ring span { color:#aaa6c1; font-size:.76rem; }
    .empty-state { text-align:center; padding:2.1rem 1rem 1.2rem; }
    .empty-state h3 { margin:.6rem 0 .3rem; }
    .empty-state p,.quiet-note,.chart-empty { color:#a5a2bd; }
    .empty-icon { margin:auto; width:56px; height:56px; border-radius:18px; display:grid; place-items:center; background:linear-gradient(135deg,rgba(167,139,250,.2),rgba(56,189,248,.14)); color:#d5c7ff; font-size:1.3rem; }
    .chart-empty { min-height:180px; display:grid; place-items:center; text-align:center; }
    .quiet-note { padding:.85rem 1rem; border:1px dashed rgba(191,176,255,.18); border-radius:12px; background:rgba(22,20,34,.5); }
    .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] { background:linear-gradient(110deg,#7954d8,#426ee5) !important; border:1px solid rgba(206,191,255,.32) !important; box-shadow:0 5px 18px rgba(91,70,202,.22); transition:filter .18s ease,transform .18s ease; }
    .stButton > button:hover { filter:brightness(1.12); transform:translateY(-1px); border-color:rgba(190,174,255,.38); }
    [data-testid="stChatMessage"] { border:1px solid rgba(191,176,255,.14); border-radius:15px; background:rgba(24,22,36,.78); padding:.75rem 1rem; }
    [data-testid="stChatInput"] { border-color:rgba(167,139,250,.35) !important; background:rgba(22,20,34,.92) !important; }
    [data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#9b75f5,#50b7f4) !important; }
    [data-testid="stExpander"] { border-color:rgba(191,176,255,.13); border-radius:12px; background:rgba(19,18,29,.5); }
    .stTextInput input,.stTextArea textarea,.stSelectbox [data-baseweb="select"],.stDateInput input,.stTimeInput input { background:#151320 !important; }
    @media (max-width:760px) { .block-container { padding:1.1rem 1rem 3rem; } .hero { padding:1.35rem; border-radius:16px; } .hero-mark { width:70px; height:70px; flex-basis:70px; font-size:1.8rem; border-radius:22px; } h1 { font-size:1.85rem !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        "<div class='brand-lockup'><div style='display:flex;align-items:center;gap:12px;padding:.2rem 0 1.1rem'>"
        "<div style='width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,#8b5cf6,#3b82f6);font:700 1.15rem Space Grotesk;color:white;box-shadow:0 8px 24px #7048c944'>C#</div>"
        "<div><div style='font:700 1rem Space Grotesk;color:#f6f3ff'>NEXUS</div><div style='font-size:.72rem;color:#9691ac'>INTERVIEW STUDIO</div></div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='eyebrow'>WORKSPACE</div>", unsafe_allow_html=True)
    if "nav_choice" not in st.session_state:
        st.session_state.nav_choice = NAV_BY_NAME["Dashboard"]
    nav_choice = st.radio(
        "Main navigation",
        list(NAV_LABELS),
        format_func=lambda label: label,
        key="nav_choice",
        label_visibility="collapsed",
    )
    current_page = NAV_LABELS[nav_choice]

    st.divider()
    st.markdown("<div class='eyebrow'>CHAT HISTORY</div>", unsafe_allow_html=True)
    history_mode = "Mock interview" if current_page == "Mock Interviews" else "AI tutor"
    sessions, active = get_conversation(history_mode)
    session_ids = [session["id"] for session in sessions]
    chosen_session = st.selectbox(
        "Recent conversations",
        session_ids,
        index=session_ids.index(active["id"]),
        format_func=lambda item: next(session["title"] for session in sessions if session["id"] == item),
        key=f"sidebar_chat_history_{history_mode}",
        label_visibility="collapsed",
    )
    if chosen_session != active["id"]:
        st.session_state[f"active_session_{history_mode}"] = chosen_session
        st.rerun()
    if st.button("New conversation", width="stretch", icon=":material/add:", key="sidebar_new_conversation"):
        new_id = f"{history_mode.lower().replace(' ', '-')}-{datetime.now().timestamp()}"
        sessions.insert(0, {"id": new_id, "title": "New conversation", "messages": []})
        st.session_state[f"active_session_{history_mode}"] = new_id
        st.rerun()

    st.divider()
    with st.expander("Tutor preferences", expanded=False):
        api_key_input = st.text_input(
            "Google AI Studio API key", type="password", value="", key="api_key_input",
            help="Create a Gemini API key in Google AI Studio, or define GEMINI_API_KEY in your local .env file.",
        )
        api_key = api_key_input or os.getenv("GEMINI_API_KEY", "")
        model_name = st.text_input("Model", value=DEFAULT_MODEL, key="model_name").strip()
        experience = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"], key="experience")
        target_role = st.text_input("Target role", value="C# / .NET Developer", key="target_role")
    if "api_key" not in locals():
        api_key = os.getenv("GEMINI_API_KEY", "")
        model_name = DEFAULT_MODEL
        experience = "Beginner"
        target_role = "C# / .NET Developer"

    smtp = get_smtp_settings()
    email_ready = all(smtp.values())
    st.caption("Email reminders · " + ("Connected" if email_ready else "Configure in `.env`"))
    st.caption("Local learning studio · v1.0")

tasks = list_tasks()
roadmap_progress = get_roadmap_progress()
activity = get_activity(days=7)
quiz_stats = get_quiz_stats()
pending_tasks = [task for task in tasks if not task["completed"]]
now = datetime.now().replace(microsecond=0)
overdue = [task for task in pending_tasks if datetime.fromisoformat(task["due_at"]) < now]
due_soon = [task for task in pending_tasks if now <= datetime.fromisoformat(task["due_at"]) <= now + timedelta(hours=24)]

if overdue or due_soon:
    alerts = []
    if overdue:
        alerts.append(f"{len(overdue)} overdue")
    if due_soon:
        alerts.append(f"{len(due_soon)} due within 24 hours")
    st.warning(" · ".join(alerts) + " — review your study plan on the dashboard.", icon=":material/notifications_active:")

if current_page == "Dashboard":
    render_dashboard(tasks, roadmap_progress, activity, quiz_stats, api_key, email_ready, smtp)
elif current_page == "AI Chat":
    render_chat("AI tutor", api_key, model_name, experience, target_role)
elif current_page == "Daily Training":
    render_daily_training(api_key)
elif current_page == "Learning Roadmap":
    render_roadmap()
elif current_page == "Interview Questions":
    render_interview_questions()
elif current_page == "Coding Practice":
    render_coding_practice()
elif current_page == "Mock Interviews":
    render_chat("Mock interview", api_key, model_name, experience, target_role)
elif current_page == "Progress Analytics":
    render_analytics(tasks, roadmap_progress, activity, quiz_stats)
elif current_page == "Settings":
    render_settings(api_key, model_name, experience, target_role, email_ready, smtp)

st.markdown(
    "<div style='border-top:1px solid rgba(191,176,255,.1);margin-top:2.5rem;padding-top:1rem;color:#77738e;font-size:.75rem'>"
    "NEXUS · C# INTERVIEW STUDIO <span style='float:right'>Built for focused practice</span></div>",
    unsafe_allow_html=True,
)