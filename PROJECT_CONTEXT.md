# EchoTask shared project context

This file is the concise source of truth for ChatGPT and Codex. Keep
`Echotask/echotask-frontend/UIPlain.md` as a separate brainstorming/design-note
file; promote only settled product decisions here.

## Project purpose

EchoTask is an internal caretaking-operations web app. It gives workers,
coordinators, and supervisors a shared view of attendance, area coverage,
temporary assignments, events, snow logs, and supply requests. The MVP uses a
React/Vite frontend and a Flask/Flask-SQLAlchemy backend with SQLite.

## Verified Git and backend checkpoint

- Current working branch: `feature/ui-mvp`.
- `main` baseline commit: `4dd719b54c3365af03f266c4bd04ddf54b50a57e`.
- The backend MVP is merged into `main`.
- The `seeds.py` merge conflict was resolved with the backend MVP version.
- At that checkpoint, `git diff --check` passed and the full backend unit suite
  passed: 52 tests, OK.

## Frontend baseline

- `Echotask/echotask-frontend` is a Vite/React 19 app using React Router.
- Startup bootstraps the Flask session through `GET /auth/me`; unauthenticated
  users receive the login view, and authenticated users enter the app shell.
- The reusable shell provides Dashboard, Attendance, Supplies, Snow Logs, and
  Events navigation. Accounts appears only for supervisors, matching backend
  authorization.
- The working supplies-request prototype and its components must be preserved
  and is reachable at `/supplies`. It still uses mock supply data and a
  simulated submit action; backend integration is future work.
- The Dashboard contains honest empty/not-connected states for operations,
  availability, area coverage, and events; it does not expose absence reasons.

## Current UI product direction

- Build a clear role-aware application shell with navigation to operational
  areas such as the dashboard, attendance, assignments/coverage, events, snow
  logs, and supplies.
- The primary dashboard/map should communicate daily attendance/availability
  and which worker covers each area, including temporary coverage.
- Selecting an area may reveal its regular worker and current coverage, but the
  dashboard must never expose private absence reasons.
- Snow-log records and supply requests belong on dedicated pages. Events need a
  visible reminder surface plus coordinator/supervisor management UI.
- `UIPlain.md` remains the raw idea backlog; it is not an approved detailed UI
  specification.

## Current UI milestone and implementation order

The first **UI Foundation** slice is complete and frontend lint/build pass. It
added:

- Centralized native-fetch API/session helpers under `src/api`, always using
  `credentials: 'include'`.
- React Router routes, authenticated app shell, login/logout/session bootstrap,
  role-aware navigation, Dashboard foundation, and placeholder feature views.
- A Vite `/api` development proxy to Flask on `localhost:5000`, rewriting the
  prefix so existing root-level backend route paths remain unchanged.
- `react-router-dom` as the only new frontend dependency.

No backend files, configuration, dependencies, or behavior were changed.

The UI Foundation end-to-end integration checkpoint is also verified. Using an
isolated database populated by the existing `seed-core-data` command, the Vite
development server successfully proxied the complete Flask session flow:
unauthenticated rejection, invalid-login rejection, valid login, persisted
session identity, logout, and post-logout rejection. The SPA root and a direct
feature-route entry both loaded through Vite, and frontend account visibility
matches the backend's supervisor-only account-management authorization.

The **Worker Attendance / Check-in UI** milestone is complete. Attendance now
uses the existing backend API: workers fetch their own current-day record,
check in once, and refetch authoritative state after reloads or duplicate
conflicts. Coordinators and supervisors receive a read-only current-day summary
that omits absence reasons and correction metadata; management tools remain a
later milestone. The integration was verified through the Vite proxy with an
isolated seeded database, including 401, 201, and duplicate 409 behavior. No
backend files or behavior changed.

The **Dashboard Today's Worker Availability** milestone is complete.
Coordinator and supervisor dashboards use
`GET /workers/availability?date=YYYY-MM-DD` to show active workers, regular
areas, backend-derived operational status, and temporary assignment
destinations. Assignment-derived `Assigned elsewhere` status takes precedence
over attendance. The UI includes loading, retryable error, empty, and responsive
list states; workers retain the existing simple dashboard. Only operational
fields are rendered, and assignment notes or private attendance data are not
shown. Frontend lint, production build, and `git diff --check` pass. The focused
availability backend test could not run in the available system Python because
Flask is not installed; no backend files or behavior changed.

## Important backend and UI constraints

- Authentication is server-side session based: `POST /auth/login`,
  `GET /auth/me`, and authenticated `POST /auth/logout`. The frontend must send
  session cookies with API requests and treat 401 and 403 distinctly.
- Roles are `worker`, `coordinator`, and `supervisor`. Workers handle their own
  check-in and submissions; coordinators manage operational records;
  supervisors inherit coordinator capabilities and manage accounts and supply
  processing.
- `GET /workers/availability?date=YYYY-MM-DD` provides shared worker status,
  regular area, and temporary assignments. Shared availability is limited to
  `Working`, `Away`, and `Assigned elsewhere`; absence reasons are private and
  must not appear in shared dashboard/map UI.
- Buildings contain regular work areas. A worker has one regular area;
  coordinators and supervisors do not. Temporary, date-only assignments can
  include multiple workers without changing regular areas.
- Attendance has one official record per worker and date. Events belong to
  buildings. Snow logs use reusable, deactivatable locations within areas.
  Supply requests permanently retain their submitted area and line items;
  statuses are `Submitted` and `Completed`.
- Accounts and snow-log locations are deactivated when history must be
  preserved.
- Do not expand the backend into detailed individual daily task/work-order
  management unless a concrete UI requirement demonstrates the need.
- Backend conventions remain: application factory and shared SQLAlchemy
  instance, explicit `*_id` keys, validated JSON with appropriate status codes,
  explicit/non-inferential schema upgrades, and password hashes only. The demo
  seed password is `demo`. See the backend README for the full API and setup.

## Verification policy

- Do not rerun the 52 backend tests during frontend-only work.
- Rerun backend tests only when backend code, configuration, or dependencies
  change.
- For completed frontend milestones, run `npm run lint` and `npm run build` from
  `Echotask/echotask-frontend`.
- Avoid repeated setup checks and unnecessary verification; choose checks in
  proportion to the files changed.

## Next action

Continue with the next smallest Dashboard slice: a read-only **Today's Events**
reminder surface for coordinator and supervisor users, using the existing event
API and preserving the simple worker dashboard unless product requirements call
for worker visibility.
