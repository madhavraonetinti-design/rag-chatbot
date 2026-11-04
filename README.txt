C# INTERVIEW COACH
===================

A Streamlit chatbot that helps you prepare for C# and .NET interviews. It explains concepts, runs practice interviews, reviews your answers, and tracks a preparation plan. Tutor responses use an OpenAI-compatible API. Tasks are stored locally in SQLite. Due dates produce in-app alerts, and optional email reminders use SMTP.

FEATURES
--------
- Streaming tutor chat with selectable experience level and target role.
- Practice C#, .NET, LINQ, async/await, coding, system design, and behavioral interviews.
- Local persistent preparation tasks in SQLite.
- In-app alerts for overdue tasks and tasks due within 24 hours.
- Optional email reminders sent on user action.
- API and SMTP credentials loaded from a local .env file.

REQUIREMENTS
------------
- Python 3.10 or later
- VS Code with the Python extension
- An OpenAI API key with access to the selected model
- SMTP account settings only if email reminders are wanted

INSTALL ON WINDOWS
------------------
Open this folder in VS Code and run these commands in its PowerShell terminal:

    py -3.10 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

If PowerShell blocks activation:

    py -3.10 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

The workspace may already include env1. To use it, select env1\Scripts\python.exe with the VS Code command Python: Select Interpreter, then run:

    .\env1\Scripts\python.exe -m pip install -r requirements.txt

CONFIGURE THE AI API KEY
------------------------
Copy the example file and edit the copy:

    Copy-Item .env.example .env

Replace your_api_key_here in .env with your API key. Keep the key private. The .env file is ignored by Git. Alternatively, enter the key in the app sidebar for the current session.

The default model is gpt-4o-mini. Change OPENAI_MODEL in .env or the app sidebar to use another compatible model available to your account. API usage may incur charges; check provider pricing and limits.

OPTIONAL EMAIL REMINDERS
------------------------
Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM in .env. Gmail example:

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=you@example.com
    SMTP_PASSWORD=your-provider-app-password
    SMTP_FROM=you@example.com

Use a provider-issued app password or SMTP credential, not your normal email password. Without SMTP configuration, the task planner and in-app alerts still work. Emails are only sent after selecting Send due email reminders; they are not sent automatically in the background. Only tasks with a reminder email address that are overdue or due within 24 hours are eligible. Sent reminders have a 24-hour cooldown.

RUN THE APP
-----------
Run in the VS Code terminal:

    streamlit run app.py

Open the local address printed by Streamlit, usually http://localhost:8501.

USAGE
-----
1. Enter an API key in the sidebar or configure OPENAI_API_KEY in .env.
2. Choose your experience level and target role.
3. Ask a C#/.NET question or pick a suggested practice prompt.
4. Open Preparation plan to add tasks and due dates.
5. Mark finished tasks complete. Review in-app due and overdue alerts.
6. Configure SMTP and select Send due email reminders when reminders are needed.

DATA AND PRIVACY
----------------
Tasks are stored locally at data/tutor_tasks.sqlite3. The data folder is excluded from Git. Chat prompts are sent to the configured AI API provider. API and SMTP credentials are not stored in the task database. Review provider data and retention terms before entering sensitive information.

TROUBLESHOOTING
---------------
- Missing API key: configure OPENAI_API_KEY in .env or enter it in the sidebar.
- API/model error: verify the key, model access, account billing, and provider limits.
- Email failure: check SMTP values and provider app password. Port 587 uses STARTTLS; 465 uses SSL.
- Missing tasks: do not delete data/tutor_tasks.sqlite3; it is local app data and is intentionally excluded from Git.