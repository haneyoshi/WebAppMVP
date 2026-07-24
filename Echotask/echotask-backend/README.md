# EchoTask backend

Flask and SQLAlchemy API for EchoTask's caretaking operations MVP.

## Local setup

```powershell
cd Echotask\echotask-backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_APP = "run.py"
flask run
```

Set `SECRET_KEY` in `.env` or the environment before using login sessions. Set
`SESSION_COOKIE_SECURE=true` when serving over HTTPS. The SQLite database defaults
to `instance/echotask.db`; `DATABASE_URL` can override it.

The public endpoints are:

- `POST /auth/login`
- `GET /ping`

All other API endpoints require the session cookie returned by login.

## Development data

Seed commands use `demo` as the development password, but store only its Werkzeug
hash.

The CSV core-data seed creates `bob@example.com` (coordinator) and
`sara@example.com` (supervisor), both with the development password `demo`.

```powershell
flask seed-core-demo
flask seed-supplies --csv-path Supply_Item_List.csv
flask seed-sample-request
```

For a database created by the earlier MVP schema, run the explicit upgrade once:

```powershell
flask upgrade-schema
```

The command is additive, creates the event and assignment tables, updates legacy
`pending` supply statuses to `Submitted`, and hashes only literal legacy `demo`
passwords. It refuses to continue if legacy supply requests lack an area because
their historical areas cannot be inferred safely.

## Roles and workflows

- Workers check in once daily, view their private attendance, submit supplies for
  their regular area, submit completed snow logs, and view shared operations.
- Coordinators manage official attendance, temporary assignments, events, and
  snow-log locations, and can view operational records and all supply requests.
- Supervisors inherit coordinator access, manage user accounts, process supply
  requests, and view supply summaries.
- Accounts are deactivated rather than deleted so related history is preserved.
- Shared availability exposes only `Working`, `Away`, or `Assigned elsewhere`.
  Absence reasons are available only in private attendance responses.

Supply-request statuses are `Submitted` and `Completed`.

## Main API routes

| Area | Routes |
| --- | --- |
| Session | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| Locations | `GET /buildings`, `GET /buildings/<id>`, `GET /areas`, `GET /areas/<id>` |
| Users | `GET /users`, `GET /users/<id>`, supervisor account create/update/deactivate |
| Availability | `GET /workers/availability?date=YYYY-MM-DD` |
| Attendance | worker `POST /attendance/check-in`; official `GET/POST/PATCH /attendance...` |
| Assignments | `GET /assignments`; coordinator/supervisor `POST` and `PUT` |
| Supplies | `GET /supplies/items`, `GET/POST /supplies/requests`, status and summary routes |
| Snow | `/snow-log-locations` and `/snow-logs` list/detail/create/management routes |
| Events | `/events` list/detail/create/update/delete routes |

JSON validation errors use `{"error": "..."}`. Authentication failures return
401, role failures 403, missing records 404, and uniqueness conflicts 409.

## Tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use isolated temporary or in-memory SQLite databases and do not modify the
development database.
