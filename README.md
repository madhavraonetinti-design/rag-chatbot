# NEXUS · C# Interview Studio

A presentation-ready C# and .NET interview preparation workspace built with Streamlit. It combines an API-powered AI tutor, mock interviews, a persistent learning roadmap, technical and behavioral practice, scored quizzes, coding challenges, progress analytics, and optional task-reminder email.

## Workspace

- **Dashboard:** real task and roadmap totals, overall progress, daily learning-action goal, seven-day activity chart, upcoming tasks, and recent activity.
- **AI Chat:** streaming C#/.NET tutoring with session-scoped chat history and suggested prompts.
- **Daily Training:** a dated .NET learning assignment with objectives, a hands-on exercise, completion tracking, and recent lesson history.
- **Learning Roadmap:** ten milestones with persistent Not started, In progress, and Completed states.
- **Interview Questions:** technical answer guides, STAR-style behavioral prompts, and beginner/intermediate/advanced scored quizzes.
- **Coding Practice:** editable C# challenges with a real local .NET compiler/test harness.
- **Mock Interviews:** separate AI interview sessions; selected behavioral questions carry into the mock room.
- **Progress Analytics:** persisted learning-action trends, quiz accuracy, roadmap, and task progress.
- **Settings:** API connection test and email configuration status.

## Requirements

- Python 3.10 or newer
- VS Code with the Python extension
- A Google AI Studio Gemini API key (default model: `gemini-2.5-flash`)
- .NET 8 SDK for running coding-practice submissions
- Gmail SMTP credentials if you want scheduled daily assignment emails

## Windows setup

Open the project folder in VS Code. In the integrated PowerShell terminal, create a virtual environment and install packages:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked, call the environment's Python directly:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

To use the existing `env1` environment, select `env1\Scripts\python.exe` with **Python: Select Interpreter**, then run:

```powershell
.\env1\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure Google AI Studio

Copy the safe example and edit the local copy:

```powershell
Copy-Item .env.example .env
```

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey). Set `GEMINI_API_KEY` in `.env`, or enter the key in the app's Settings sidebar for the current session. Never commit or share the real key; `.env` is excluded by `.gitignore`. The default model is `gemini-2.5-flash`; change `GEMINI_MODEL` if needed. API usage is subject to Google's quotas and pricing.

## Daily training and Gmail notifications

The app rotates through a structured C#/.NET curriculum and creates one stable assignment per date. Its daily Gmail digest includes that lesson plus incomplete tasks that are overdue or due within 24 hours. To enable it, configure `.env`:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM=you@example.com
DAILY_TRAINING_EMAIL=learner@example.com
DAILY_TRAINING_HOUR=8
DAILY_TRAINING_MINUTE=0
DAILY_TRAINING_TIMEZONE=local
```

For Gmail, enable 2-Step Verification and create an App Password in Google Account security settings. Use that generated app password in `SMTP_PASSWORD`, not your normal Gmail password. Set `SMTP_USERNAME` and `SMTP_FROM` to the sending account and `DAILY_TRAINING_EMAIL` to the recipient address. The sender and recipient can be the same.

The schedule uses 24-hour time. `DAILY_TRAINING_TIMEZONE=local` uses the computer's timezone; you may also set an IANA timezone such as `America/New_York`. Restart the app after editing `.env`. The Daily Training and Settings pages show whether scheduling is active, and Settings offers a button to send today's digest immediately. Each date's assignment is sent at most once, and included tasks receive a 24-hour reminder cooldown.

**The computer and Streamlit server must stay running at the scheduled time.** This scheduler runs inside the app; it cannot send email while the computer is off. To receive messages while the computer is off, deploy the app on an always-on server or configure an external scheduled job. Gmail SMTP uses STARTTLS on port 587; port 465 uses SSL.

Existing task reminders still work: add an email address when creating a task and select **Send due email reminders** when a task is overdue or due within 24 hours.

## Run

In the VS Code terminal:

```powershell
streamlit run app.py
```

Open the local URL Streamlit prints, usually `http://localhost:8501`.

## Coding practice setup

Install the [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) to compile and run challenge submissions. The app creates a temporary console project, runs its tests, and removes that project afterward. Submitted code executes locally without a sandbox; only run code you trust. Without the SDK, the page displays an installation hint and does not fabricate test results.

## Data and privacy

Tasks, daily assignments, reminder status, roadmap status, quiz scores, and learning activity are stored in the local `data/tutor_tasks.sqlite3` database. `data/`, `.env`, and Python environments are excluded from Git. Chat history stays in the active Streamlit session and prompts are sent to Google AI Studio's Gemini API. Review Google's data and retention terms before entering sensitive information.