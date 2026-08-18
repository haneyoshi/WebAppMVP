# EchoTask

EchoTask is a portfolio-ready caretaking operations MVP for workers,
coordinators, and supervisors. It combines attendance, worker availability,
temporary area coverage, events, Snow Logs, supply requests, and account
management in a React frontend backed by a Flask API and SQLite.

## Required tools and optional development tools

Required:

- Git, to clone the repository
- Python 3.9 or newer, including `pip` and `venv`
- Node.js 20 or newer, including npm
- A modern web browser

This project uses SQLite through Flask-SQLAlchemy. SQLite support is included
with Python, so no separate database server is required. MySQL and PostgreSQL
are not required.

No editor, browser, or API-client extension is required. VS Code, Codex,
ChatGPT, Postman, Thunder Client, Live Server, SQLite Viewer, Flask extensions,
and React extensions are all optional development conveniences only. Python
packages are installed from `requirements.txt`; frontend packages are installed
from `package-lock.json` with npm.

The completed project has been verified with Python 3.13 and Node.js 22. The
minimum versions above match the installed Flask and Vite toolchains.

## Clone the repository

```powershell
git clone <repository-url>
cd WebAppMVP
```

Replace `<repository-url>` with this repository's Git URL.

## Backend setup

Open a terminal in the backend directory:

```powershell
cd Echotask\echotask-backend
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, allow local scripts for that one
terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with:

```bash
source .venv/bin/activate
```

Install the backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Copy the safe environment template to `.env`:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env`. Replace the example
`SECRET_KEY` value with a long random local-development value. Do not commit
`.env`. The default `DATABASE_URL` uses the ignored local SQLite file at
`instance/echotask.db`.

For a fresh database, initialize the schema and load the canonical portfolio
data:

```powershell
$env:FLASK_APP = "run.py"
flask upgrade-schema
flask seed-core-data
flask seed-supplies --csv-path Supply_Item_List.csv
```

On macOS or Linux, set Flask's entry point with `export FLASK_APP=run.py`.
`seed-core-data` is the single canonical reset: it restores the supplied UofM
workplace dataset with 10 buildings, 22 operational areas, the 22 supplied
worker names, one regular worker per area, and the coordinator and supervisor
accounts. It resets core and operational data, so do not run it against a
database whose local records must be preserved.

Start the backend:

```powershell
flask run
```

The API runs at `http://localhost:5000`. Leave this terminal open.

## Frontend setup

Open a second terminal from the repository root:

```powershell
cd Echotask\echotask-frontend
npm install
npm run dev
```

No frontend `.env` file is required for the standard local setup: the app
defaults to `VITE_API_URL=/api`, matching Vite's included Flask proxy. If that
URL must be customized, copy `.env.example` to `.env` in the frontend directory
and edit only `VITE_API_URL`.

If Windows PowerShell blocks `npm.ps1`, either apply the same process-scoped
execution-policy command shown above or run `npm.cmd install` and
`npm.cmd run dev`.

Open `http://localhost:5173` in a browser. The Vite development server proxies
`/api` requests to the Flask backend at `http://localhost:5000`.

## Demo accounts

These intentionally public credentials are for local portfolio authentication
only. They do not indicate dummy workplace data: displayed worker identities,
buildings, areas, and assignments come from the supplied canonical dataset.
Every canonical seeded account uses the password `demo`.

| Role | Account/email | Password | What a reviewer can explore |
| --- | --- | --- | --- |
| Worker | `user1@example.com` | `demo` | Personal check-in, team availability, supply requests, and Snow Log submission |
| Coordinator | `bob@example.com` | `demo` | Attendance management, assignments, events, Snow Log locations/history, and supply review |
| Supervisor | `sara@example.com` | `demo` | Coordinator workflows plus account management and supply-request processing |

## Stop and restart

Press `Ctrl+C` in each server terminal to stop it. Restart the backend with
`flask run` from the activated backend environment and restart the frontend
with `npm run dev` from the frontend directory. The SQLite data remains in
`instance/echotask.db` between restarts.

More backend commands and API details are in
[`Echotask/echotask-backend/README.md`](Echotask/echotask-backend/README.md).
