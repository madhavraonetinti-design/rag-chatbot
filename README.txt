C# INTERVIEW STUDIO
===================

A premium dark-mode Streamlit workspace for C# and .NET interview preparation.

PAGES
-----
- Dashboard: real task/roadmap progress, daily goal, weekly activity, and upcoming tasks.
- Daily Training: one dated .NET objective and exercise, completion tracking, and lesson history.
- AI Chat: streaming AI tutor with session chat history.
- Learning Roadmap: 10 persistent C#/.NET learning milestones.
- Interview Questions: technical answer guides, STAR behavioral prompts, and scored quizzes.
- Coding Practice: editable challenges with a real local .NET compiler and test harness.
- Mock Interviews: AI-led conversational interview practice.
- Progress Analytics: saved quiz, task, roadmap, and activity data.
- Settings: AI API health check and SMTP configuration status.

REQUIREMENTS
------------
- Python 3.10 or newer and VS Code with the Python extension.
- Google AI Studio Gemini API key (default model gemini-2.5-flash).
- .NET 8 SDK for running C# challenge code.
- Gmail SMTP App Password is needed for scheduled daily email notifications.

WINDOWS INSTALLATION
--------------------
Open a PowerShell terminal in VS Code:

    py -3.10 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

If activation is blocked:

    py -3.10 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Existing env1 environment:

    .\env1\Scripts\python.exe -m pip install -r requirements.txt

Select env1\Scripts\python.exe with Python: Select Interpreter in VS Code.

GOOGLE AI STUDIO API KEY
------------------------
Copy .env.example to .env:

    Copy-Item .env.example .env

Create a Gemini API key at https://aistudio.google.com/app/apikey. Put it in GEMINI_API_KEY. Never commit or share the real key. .env is ignored by Git. You may instead enter the key in the app Settings for the current session. The default model is gemini-2.5-flash; set GEMINI_MODEL to change it. Usage follows Google's quotas and pricing.

DAILY TRAINING AND GMAIL NOTIFICATIONS
--------------------------------------
The app rotates through a C#/.NET curriculum and saves one assignment per date. The daily Gmail message includes that lesson plus incomplete tasks due in the next 24 hours or overdue. To enable it, configure .env:

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=you@example.com
    SMTP_PASSWORD=your-google-app-password
    SMTP_FROM=you@example.com

    DAILY_TRAINING_EMAIL=learner@example.com
    DAILY_TRAINING_HOUR=8
    DAILY_TRAINING_MINUTE=0
    DAILY_TRAINING_TIMEZONE=local

For Gmail, enable 2-Step Verification and create an App Password in Google Account security settings. Use it in SMTP_PASSWORD, not your normal Gmail password. Set SMTP_USERNAME and SMTP_FROM to the sending account and DAILY_TRAINING_EMAIL to the recipient.

The schedule uses 24-hour time. DAILY_TRAINING_TIMEZONE=local uses the computer timezone; an IANA zone such as America/New_York can also be used. Restart Streamlit after editing .env. Daily Training and Settings show whether scheduling is enabled. Settings can send today's digest immediately. The same day's assignment is sent at most once; included tasks have a 24-hour email cooldown.

The computer and Streamlit server must be running at the scheduled time. This scheduler runs inside the app and cannot send email while the computer is off. Use an always-on deployment or an external scheduled job if needed. Gmail SMTP port 587 uses STARTTLS; port 465 uses SSL.

Existing task reminders are also available: add an email to a task and select Send due email reminders when it is overdue or due within 24 hours.

RUN
---

    streamlit run app.py

Open the URL printed by Streamlit, normally http://localhost:8501.

CODING PRACTICE
---------------
Install .NET 8 SDK from https://dotnet.microsoft.com/download/dotnet/8.0. The app builds and runs a temporary C# console project to execute challenge tests, then removes it. Code executes locally without a sandbox; run only code you trust. Without the SDK, the app explains how to install it and does not claim tests passed.

DATA AND PRIVACY
----------------
Tasks, daily assignments, email status, roadmap progress, quiz scores, and activity are stored in data/tutor_tasks.sqlite3 and excluded from Git. Chat history stays in the active Streamlit session; prompts are sent to Google AI Studio's Gemini API. Check Google's data and retention terms before entering sensitive data.