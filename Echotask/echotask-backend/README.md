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

`seed-core-data` is the single canonical base reset. It restores the supplied
UofM workplace structure with 10 named buildings, 22 named areas, the 22 supplied
worker names with one regular worker per area, the two management accounts
below, and a small deterministic set of active Snow Log locations. It does not
create attendance, assignments, events, Snow Log submissions, supply requests,
or supply items.

All canonical accounts use the development password `demo`, stored only as a
Werkzeug hash:

- `bob@example.com` — coordinator
- `sara@example.com` — supervisor
- `user1@example.com` through `user22@example.com` — workers

For a safe fresh demo, run these commands in order:

```powershell
flask seed-core-data
flask seed-supplies --csv-path Supply_Item_List.csv
```

To build a separate portfolio database without touching the default development
database, set `DATABASE_URL` only for the seeding session:

```powershell
$env:DATABASE_URL = "sqlite:///instance/echotask-portfolio.db"
flask seed-core-data
flask seed-supplies --csv-path Supply_Item_List.csv
flask seed-portfolio-demo-day
Remove-Item Env:DATABASE_URL
```

The resulting ignored local file is `instance/echotask-portfolio.db`. Start Flask
with the same `DATABASE_URL` value when using that database for portfolio demos.
Removing the override returns later Flask commands to the normal configured
development database.

`seed-portfolio-demo-day` is only for that dedicated portfolio database and does
not replace the canonical `seed-core-data` plus `seed-supplies` setup. It verifies
the exact portfolio database path and canonical dataset before replacing the
demo-day attendance, assignments, events, supply requests, and Snow Logs. It
preserves buildings, areas, accounts, Snow Log locations, and the supply catalog,
and refuses to run against the normal development database.

`seed-core-data` is destructive to the core and operational tables it resets.
Do not run it against records that need to be preserved. Supply-item seeding is
intentionally separate; `seed-supplies` adds missing catalog items and skips
duplicates.

The obsolete generic core-data helper has been removed so normal setup cannot
create placeholder buildings, areas, or workers. `seed-sample-request` is
optional and creates operational sample data, so it is not part of the fresh
canonical sequence.

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
| Assignments | `GET /assignments`; coordinator/supervisor `POST`, `PUT`, and `DELETE` |
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
