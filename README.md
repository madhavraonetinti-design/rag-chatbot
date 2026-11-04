# C# Interview Coach

A Streamlit chatbot that helps you prepare for C# and .NET interviews. It explains concepts, runs practice interviews, reviews your answers, and tracks a preparation plan. It uses an OpenAI-compatible API for tutor responses, SQLite for local tasks, in-app due alerts, and optional SMTP email reminders.

## Features

- Streaming tutor chat with selectable experience level and target role
- Practice for C#, .NET, LINQ, async/await, coding, system design, and behavioral interviews
- SQLite-backed preparation tasks that remain on this computer
- In-app alerts for overdue tasks and tasks due within 24 hours
- Optional email reminders sent when you select the reminder button
- API keys and SMTP passwords loaded from local environment variables

## Requirements

- Python 3.10 or later
- VS Code with the Python extension
- An OpenAI API key with access to the selected model
- SMTP account settings only if you want email reminders

## Setup on Windows

Open the project folder in VS Code. In the integrated PowerShell terminal, create a virtual environment and install dependencies:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the environment's Python directly:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The workspace may already have an `env1` environment. To use it, select `env1\Scripts\python.exe` with **Python: Select Interpreter**, then run:

```powershell
.\env1\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure the AI API key

Copy the example environment file and edit the copy:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `your_api_key_here` with your API key. Keep the key private. `.env` is ignored by Git and should never be committed. You can also enter the API key in the app's sidebar for the current Streamlit session.

The default model is `gpt-4o-mini`. Change `OPENAI_MODEL` in `.env` or the model field in the sidebar if your API account uses another compatible model. API usage may incur provider charges; check your provider's pricing and limits.

## Optional email reminders

In `.env`, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM`. Example settings for Gmail are:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=your-provider-app-password
SMTP_FROM=you@example.com
```

Use an app password or provider-issued SMTP credential, not your normal email password. Email settings are optional. Without them, the in-app overdue and due-soon alerts and task planner still work. Email reminders are sent only when you select **Send due email reminders**; tasks are not emailed automatically in the background. A task needs a reminder email address and must be overdue or due within 24 hours. Successful reminders have a 24-hour cooldown.

## Run in VS Code

In the integrated terminal, run:

```powershell
streamlit run app.py
```

Open the local address Streamlit prints, usually `http://localhost:8501`.

## Use the tutor

1. In the sidebar, enter an API key or configure `OPENAI_API_KEY` in `.env`.
2. Choose your experience level and target role.
3. Use a suggested prompt or ask a C#/.NET interview question in the chat.
4. Open **Preparation plan** to add topics, coding practice, mock interviews, and due dates.
5. Mark tasks complete as you finish them. The app shows due-soon and overdue alerts.
6. Configure SMTP and select **Send due email reminders** when you want reminder emails sent.

## Data and privacy

Task information is stored locally in `data/tutor_tasks.sqlite3`; the `data/` directory is ignored by Git. Chat prompts are sent to the configured AI API provider to generate responses. The app does not store API or SMTP credentials in the task database. Review your provider's data and retention terms before using sensitive information.

## Troubleshooting

- **Missing API key:** Add `OPENAI_API_KEY` to `.env`, or enter the key in the sidebar, then rerun the app.
- **API authentication/model error:** Verify the key, model name, account access, and provider billing/limits.
- **Email not configured:** Set all SMTP fields in `.env`, restart Streamlit, and assign an email address to the task.
- **Email send failure:** Check SMTP host/port, sender permissions, and provider-issued app password. Port 587 uses STARTTLS; port 465 uses SSL.
- **Tasks are missing:** Keep `data/tutor_tasks.sqlite3`; it is local application data and is intentionally excluded from Git.