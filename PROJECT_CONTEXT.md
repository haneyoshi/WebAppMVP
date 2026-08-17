# EchoTask project context

EchoTask is an internal React and Flask application for caretaking operations.
The backend uses Flask-SQLAlchemy with SQLite for the MVP.

## Core model

- Buildings contain regular work areas.
- A worker has one regular area; coordinator and supervisor accounts do not.
- Attendance keeps one official record per worker and date.
- Temporary date-only assignments can include multiple workers without changing
  their regular areas.
- Snow logs reference reusable, deactivatable locations within areas.
- Supply requests permanently retain their submitted area and contain line items.
- Events belong to buildings.

## Roles

- Workers check in, view their own attendance, submit supplies and snow logs, and
  read shared events, assignments, regular areas, and availability.
- Coordinators manage official attendance, assignments, events, and snow
  locations and read operational records.
- Supervisors inherit coordinator capabilities and manage accounts and supply
  processing.

Accounts and snow-log locations are deactivated when history must be preserved.
Supply request statuses are `Submitted` and `Completed`. Shared availability is
limited to `Working`, `Away`, and `Assigned elsewhere`; private absence reasons
are not part of shared responses.

## Development conventions

- Use the Flask application factory and shared SQLAlchemy instance.
- Use explicit `*_id` primary and foreign-key names.
- Validate JSON bodies and return JSON errors with appropriate HTTP status codes.
- Keep database upgrades explicit; never infer historical data during migration.
- Store only password hashes. The documented seed password is `demo`.
- Run backend tests from `Echotask/echotask-backend` with:

  `.venv\Scripts\python.exe -m unittest discover -s tests -v`

See `Echotask/echotask-backend/README.md` for endpoints, setup, and schema-upgrade
instructions.
