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
- The Supplies request builder is reachable at `/supplies` and uses the real
  authenticated catalog and request APIs while preserving its original
  prototype interaction and components.
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

The **Structured Assignment Destination** backend milestone is complete.
Temporary assignments now have an optional nullable `destination_area_id` that
references an existing EchoTask area. Free-form assignments remain valid with
`destination_area_id = NULL`; `location_task` remains required and is never
matched to an area implicitly. Assignment create/read/update responses and
nested worker-availability assignments expose the destination area/building IDs
and names as flat fields. The existing SQLite `upgrade-schema` command adds the
nullable column without removing legacy assignment rows. Focused assignment,
availability, and schema-upgrade tests pass in the backend `.venv` (11 tests),
and `git diff --check` passes.

The **Today's Area Coverage Dashboard** milestone is complete. Coordinator and
supervisor dashboards show all areas, each area's regular worker availability,
and structured temporary coverage as a separate value. Free-form assignments
remain distinct and are not inferred as area coverage. Frontend lint,
production build, and `git diff --check` pass, and manual browser verification
passed as Bob Coordinator with all 22 areas rendered and no request errors.
Workers correctly appeared as Away because the development database had no
attendance records for the current day. An earlier local runtime failure was
caused solely by the development SQLite database missing
`assignments.destination_area_id`; running the existing `flask upgrade-schema`
command repaired the actual development database, with no source-code change
required for the repair.

The **Current-Day Attendance Management UI** milestone is complete.
Coordinators and supervisors see the full active-worker roster, including a
`Not recorded` state, and can create or correct today's official attendance
inline using only `Working` or `Away`. The optional private absence reason is
available only for `Away` and is explicitly cleared when a record changes to
`Working`. The worker check-in experience remains unchanged. Frontend lint,
production build, and `git diff --check` pass. Manual browser verification as
Bob Coordinator confirmed the complete create-and-correct flow with the
then-active worker record: an `Away` record with a private test reason saved and rendered on the
Attendance page, changing it to `Working` cleared the reason, and both Dashboard
Worker Availability and Area Coverage then showed the worker as `Working` in
its regular area. The private reason never appeared on the Dashboard.

The assignment API now supports coordinator/supervisor deletion through
`DELETE /assignments/<assignment_id>`. Deletion uses the ORM, removes the
assignment's worker association rows, and causes worker availability to fall
back to attendance (or `Away` when attendance is absent). Focused assignment
and availability tests pass. No assignment lifecycle, model, or schema changes
were introduced.

The **Current-Day Temporary Assignment Management UI** milestone is complete.
Coordinators and supervisors have a dedicated Assignments page for listing,
creating, editing, and removing today's structured destination-area coverage.
The form exposes only destination area, workers, and an optional note while
generating the required `Coverage` and `<Area name> coverage` API fields.
Legacy free-form assignments remain visible and read-only. Frontend guardrails
prevent a worker from receiving multiple current-day assignments or covering
their own regular area without treating `Away` as ineligible. Frontend lint,
production build, and `git diff --check` pass. Focused backend verification for
assignment deletion passes: 14 tests. Manual browser verification in the real
development environment as Bob Coordinator confirmed that the Assignments page
renders, destination-area and worker selection work, a worker is disabled when
the destination is their own regular area, and Away workers remain selectable.
Creating structured coverage for the then-active worker and area records made the worker
`Assigned elsewhere` and showed them as temporary coverage on the Dashboard.
Editing that assignment with two worker records updated both workers and the
area's temporary coverage. Removing it returned the first worker to `Working`,
the second worker to `Away`, and the affected areas to `Temporary
coverage: None assigned`.

The **Today's Event Reminders Dashboard** milestone is complete. This
frontend-only implementation is available to workers, coordinators, and
supervisors. It uses authenticated `GET /events`, preserves backend
chronological ordering, and filters client-side for events overlapping the
browser-local current day: event start is before the next local midnight and
event end is after the current local midnight. Explicit UTC timestamps are
parsed directly and displayed in browser-local time. Each reminder shows only the event title, building name,
and local start/end time; descriptions, creator information, event IDs, and
other internal metadata are omitted. Loading, retryable error, empty, and
populated states are supported. Browser verification confirmed the
`No events are scheduled today.` empty state, inclusion of same-day and
local-midnight-spanning events, exclusion of a next-day-only event, correct
local times, omitted private/internal details, and visibility for both worker
and coordinator roles. Temporary test events were deleted afterward. Frontend
lint, production build, and `git diff --check` pass. No backend tests were run
because no backend source changed.

The **Event Management UI + explicit event timestamp contract** milestone is
complete and browser-verified. Event `POST` and `PATCH` timestamps now require
explicit timezone information (`Z` or a numeric offset such as `-05:00`);
offset-free values are rejected with `400`. Accepted values are normalized to
UTC, range validation occurs after normalization, and event
list/detail/create/update responses serialize timestamps explicitly with `Z`.
Database storage remains naive UTC, no model or migration change was required,
and the existing event `DELETE` endpoint is unchanged. Focused backend event
tests pass: 11 tests; the full backend suite was not run.

The dedicated `/events` page gives every authenticated role a chronological
event list with title, building, browser-local start/end date and time, optional
description, and loading, retryable error, empty, and populated states. Workers
have read-only access with no New event, Edit, or Delete controls. Coordinators
and supervisors can create and edit events with save/cancel, building, title,
optional description, and browser-local start/end datetime inputs. Writes
convert local form values to timezone-aware UTC with `Date.toISOString()`;
editing converts backend UTC values back to browser-local `datetime-local`
values. Invalid dates and end-times not later than start-times are rejected
before submission. Event deletion in the UI remains deliberately deferred.

Dashboard Today's Event Reminders now parse explicit UTC timestamps directly
while retaining the existing browser-local today interval-overlap behavior.
Dashboard reminders continue to display only title, building, and local
start/end time; description and creator information remain absent.

Browser verification as a coordinator covered creating an event spanning local
midnight; correct event-page title, building, description, and local time;
correct Dashboard title, building, and local time without description; editing
title, building, description, start, and end; and correct propagation of all
edits to the event page and the applicable title, building, and times to the
Dashboard. Browser verification as a worker confirmed the event list remained
visible while New event, Edit, and Delete were absent. The temporary
browser-verification event was then deleted through the existing backend
`DELETE` endpoint and verified absent through `GET /events`. Frontend lint,
frontend production build, and `git diff --check` pass.

The frontend-only **Worker Snow Log Submission UI** milestone is complete and
browser-verified. On `/snow-logs`, workers use their authenticated regular
`area_id` to load snow-log locations, and the UI explicitly filters inactive
locations from submission. Workers can select an active location, provide
optional action taken and condition text, submit their own completed Snow Log,
see an in-session confirmation containing only the returned location, area,
and any provided text, and reset with **Submit another log**. The server creates
the submission timestamp, but the UI deliberately does not display it.
Multiple submissions are allowed; there is no date selection, backdating,
duplicate prevention, or worker history. Worker history is omitted because
Snow Log read endpoints are restricted to coordinators and supervisors, and a
worker cannot recover the in-session confirmation after reload. Coordinator
and supervisor review, history, filters, details, and location management
remain deferred.

Browser verification covered the initial no-active-location state, the ready
form with only the worker's active regular-area location, successful submission
with optional action and condition, confirmation content without timestamp or
history wording, and reset to a clean form while duplicate submission remained
available. Coordinator and supervisor verification confirmed the same concise
deferred state with no worker form, history, filters, or location-management
controls. The temporary verification location was subsequently deactivated
through the existing API and verified inactive while preserving the submitted
historical Snow Log relationship. Frontend lint, frontend production build,
and `git diff --check` pass. No backend tests were run because no backend source
changed.

The frontend-only **Coordinator/Supervisor Snow Log History UI** is complete and
browser-verified. Coordinators and supervisors receive a read-only list from
`GET /snow-logs` in the backend's existing newest-first order, showing worker,
snow-clearing location, area, action taken, and condition. Missing optional
action or condition text uses a neutral `Not provided` fallback. Loading,
retryable error, empty, populated, and responsive states are included. Bob
Coordinator and Sara Supervisor both displayed the same historical record with
its worker, location, area, action, and condition. Its deactivated location
displayed normally because location deactivation does not invalidate completed
work, and no timestamp was shown.

Browser verification as worker account `user1@example.com` confirmed that
workers retain the submission-only workflow without history or history
controls. Because that worker's temporary verification location is now
deactivated, the page correctly displayed `No active snow-clearing locations
are available for your area.`

Snow Log timestamps now use an explicit UTC `Z` response contract and appear in
browser-local time in coordinator/supervisor history. Historical worker,
location, and area names remain live relationship values rather than immutable
snapshots. Worker-entered action and condition text remains restricted to the
coordinator/supervisor history. The unpaginated list is acceptable for the MVP.
Filters, details, pagination, editing, and deletion remain deferred.

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
- Event create/update timestamps require `Z` or an explicit numeric timezone
  offset, are normalized to naive UTC for storage, and are serialized with `Z`.
  Range validation occurs after UTC normalization.
- Accounts and snow-log locations are deactivated when history must be
  preserved.
- Worker Snow Log submissions are not currently restricted at the API level to
  locations in the worker's regular area. The worker UI scopes location
  discovery to the authenticated `area_id`, but this frontend filtering is not
  an authorization boundary; server-side enforcement remains a backend-hardening
  consideration.
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

The **Canonical Data Setup** milestone is complete. `seed-core-data` is
the documented canonical destructive base reset. It creates 10 buildings, 22
areas, workers `user1@example.com` through `user22@example.com`, coordinator
`bob@example.com`, supervisor `sara@example.com`, and three deterministic active
Snow Log locations. Every canonical account retains the development password
`demo`, stored as a hash. No attendance, assignment, event, Snow Log submission,
supply-request, or supply-item operational records are created.

The safe fresh-demo sequence is `flask seed-core-data` followed by
`flask seed-supplies --csv-path Supply_Item_List.csv`. Supply items remain a
separate additive catalog seed and survive later core resets. `seed-core-data`
must not be run against records that need preservation because it clears the
core and operational tables in its reset scope. The obsolete generic core seed
helper is removed and cannot be used by normal setup.
Focused seed tests pass: 2 tests, including exact accounts and locations,
password authentication, repeatable reset behavior, and supply-item
preservation. `git diff --check` passes.

## Latest completed milestone

The frontend-only **Coordinator/Supervisor Snow Log Location Management UI** is
complete. The management section on `/snow-logs` loads all locations and areas,
clearly identifies each location by building and area, shows distinct Active and
Inactive badges, and supports creating, renaming, activating, and deactivating
through the existing `POST` and `PATCH /snow-log-locations` contract. Inactive
locations remain visible for reactivation. Each successful mutation refetches
the authoritative location list; backend validation, permission, and missing-
record errors are displayed without optimistic state changes. The existing
coordinator/supervisor Snow Log history remains below location management, and
the worker submission-only branch is unchanged.

Changed frontend files are `src/api/snowLogs.js`, `src/pages/SnowLogsPage.jsx`,
and `src/App.css`; this checkpoint file was also updated. Frontend lint,
production build, and `git diff --check` pass. No backend source changed and no
backend tests were run. Browser verification as Bob Coordinator confirmed the
page and layout, location creation and rename, deactivation with the inactive
location remaining visible, and reactivation. Worker verification confirmed
the existing submission experience remained available while location-management
controls and history were not exposed. A follow-up CSS cascade cleanup moved the
neutral gray Inactive badge override after the green base badge rule so inactive
locations no longer communicate active/success state; Active styling was not
changed. Frontend lint, production build, and `git diff --check` pass after the
cleanup.

The **Snow Log explicit UTC timestamp contract and management-history time
display** milestone is complete. Snow Log timestamps continue to be stored in
the existing SQLite `DateTime` column as timezone-naive UTC values created by
`utc_now()`; no schema migration or persisted-record rewrite was needed. Snow
Log create, detail, and management-list responses now serialize non-null
timestamps as ISO-8601 UTC strings ending in `Z`, for example
`2026-01-15T18:45:30Z`. A null database timestamp remains JSON `null`.

Coordinator and supervisor history parses the explicit UTC value with the
browser and displays a compact date and time using the browser's locale and
timezone. Missing or invalid values display `Time unavailable`. Workers retain
the existing submission-only UI: the submission confirmation remains
timestamp-free and management history remains inaccessible. Changed files are
`app/routes/snow_log_routes.py`, `tests/test_snow_logs.py`,
`src/pages/SnowLogsPage.jsx`, and `src/App.css`; this checkpoint file was also
updated. Focused Snow Log backend tests pass: 8 tests. Frontend lint, production
build, and `git diff --check` pass. Browser verification as a coordinator
confirmed that Snow Log history displays a date and time plausible for the
browser's local timezone without using the `Time unavailable` fallback. Worker
verification confirmed that submission still works, its confirmation remains
timestamp-free, and management history remains unavailable.

## Next action

The frontend-only **Worker Supply Request Backend Integration UI** milestone is
complete. The existing search, category accordion, quantity controls, summary,
and reusable request-builder interaction now use the authenticated backend.
`GET /supplies/items` supplies `{item_id, item_name, category, created_at}` rows
ordered by item name; the UI groups them by category and retains backend item
order within each category. Supply items have no inactive/availability field,
so every returned catalog item is selectable.

Worker submission sends `POST /supplies/requests` with the authenticated
worker's session `area_id` and only selected `{item_id, quantity}` rows whose
quantities are positive integers. There is no area selector and no submitted-
user override. The backend enforces the worker role, authenticated identity,
regular area, nonempty items, existing item IDs, and positive integer
quantities. The UI waits for the backend `201` response before showing the
returned message and request ID, then clears quantities while keeping the
catalog ready for another request. Loading, retryable catalog errors, empty
catalog, no search results, missing worker area, empty request, submission
errors, in-progress state, and confirmed success are handled explicitly.
Coordinators and supervisors receive a concise deferred state with no worker
submission controls.

Changed files are `src/App.jsx`, `src/api/supplies.js`,
`src/pages/SuppliesRequestPage.jsx`, and `src/components/SupplyItemRow.jsx`;
this checkpoint file was also updated. Frontend lint, production build, and
`git diff --check` pass. No backend code changed, so backend tests were not
rerun. The final Supply and Accounts browser checkpoint below records completed
manual verification of this flow.

## Latest completed milestone

The frontend-only **Coordinator/Supervisor Supply Request Review UI** is
complete. Coordinators and supervisors use the existing authenticated
`GET /supplies/requests` endpoint and receive its newest-first list showing the
request ID, submitted worker, persisted area, status, and line items with
quantities. Loading, retryable error, empty, and populated states are included.
Workers retain the existing request-builder workflow. Timestamp display,
filters, summaries, and status processing are not part of this slice.

Changed frontend files are `src/api/supplies.js`,
`src/pages/SuppliesRequestPage.jsx`, and `src/App.css`; this checkpoint file was
also updated. Frontend lint, production build, and `git diff --check` pass. No
backend code changed and no backend tests were run. The final Supply and Accounts
browser checkpoint below records completed manual verification of worker and
manager behavior.

## Next action

The frontend-only **Supervisor Supply Request Status Processing UI** is
complete. Supervisors can mark requests Completed or reopen them as Submitted
through the existing `PATCH /supplies/requests/<id>/status` endpoint. Each
successful mutation refetches the authoritative request list, update errors are
shown without optimistic changes, and concurrent status changes are disabled.
Coordinators retain the same read-only review list. Frontend lint, production
build, and `git diff --check` pass. The final Supply and Accounts browser
checkpoint below records completed manual verification of both status directions
and coordinator read-only behavior.

The frontend-only **Supervisor Account Management UI** is also technically
complete. The former Accounts placeholder now loads all accounts and areas from
`GET /users` and `GET /areas`. Supervisors can create worker, coordinator, and
supervisor accounts; edit name, email, role, regular worker area, and optionally
password; and deactivate/reactivate accounts through the existing account API.
The form enforces an area for workers and clears it for management roles. The
current supervisor's deactivate control is disabled, matching backend rules.
Loading, API error, empty, active/inactive, responsive, save, and cancel states
are included. New frontend files are `src/api/users.js` and
`src/pages/AccountsPage.jsx`; `src/App.jsx` and `src/App.css` were updated.
Frontend lint, production build, and `git diff --check` pass. No backend source
changed for either milestone. The final Supply and Accounts browser checkpoint
below records completed manual verification of these account workflows.

## Next action

Final technical integration verification is complete. The full backend suite
passes: 66 tests, OK. Final frontend lint and production build pass, and
`git diff --check` passes. The production build generated only the ignored
`dist/` directory. The existing ignored development `.env` and
`instance/echotask.db` remain in place; no new tracked or untracked database,
secret, key, or generated build artifact was introduced. The application is
technically ready to run using the documented Flask and Vite development setup.

The Supply and Accounts browser/visual/usability checks listed at this checkpoint
were subsequently completed and are recorded in the final checkpoint below. No
source work is currently blocked. Event deletion, supply procurement summaries/
filters and timestamps, pagination, and a graphical dashboard map remain
explicitly deferred as nonessential post-MVP enhancements.

## Next action

Start both development servers and perform the accumulated browser verification,
beginning with the worker Supply request flow because it is the oldest milestone
still awaiting a browser check. Do not reset or reseed the active development
database unless its records are intentionally disposable.

## Browser-found Supplies accordion fix

Browser verification found that every supply category expanded or collapsed
together because `SuppliesRequestPage` passed one shared `isFolded` boolean and
setter to every `CategoryAccordion`. Each accordion now owns its own initially
folded state, so toggling Garbage Bags (or any other category) changes only that
category. Search, catalog loading, quantities, request summary, submission, and
styling are unchanged. Changed frontend files are
`src/pages/SuppliesRequestPage.jsx` and
`src/components/CategoryAccordion.jsx`; this checkpoint file was also updated.
Frontend lint, production build, and `git diff --check` pass. Manual browser
reverification confirmed independent category toggles.

## Browser-found Supply Request data mismatch investigation

Browser verification reported that worker Request #1 showed one selected item
at quantity 2 before submission, while manager review later showed six unrelated
items at quantity 1. Read-only inspection confirmed that this is not a manager
rendering discrepancy: active SQLite Request #1 is the Submitted request for
user ID 1 and area ID 1, dated `2026-08-18 14:45:58.831502`, and its persisted
line rows are item IDs 69, 76, 30, 29, 68, and 1, each quantity 1. The live
authenticated `GET /supplies/requests` response returns those same six item IDs,
names, and quantities for Request #1.

The current worker UI derives both its visible summary and POST `items` payload
from the same positive-quantity `requestItems` array. The current backend
validates the submitted list, creates one request, and inserts one line for each
validated tuple. Manager code renders the response's nested `items` array
directly. No remaining frontend mock/sample request data, alternate POST route,
SQLite trigger/view, response-shape mismatch, or request/item association error
was found. The existing focused backend test already exercises a one-item,
quantity-2 POST against an isolated database. Because the browser request body
was not captured and the six persisted rows cannot be produced from that stated
payload by the inspected code, root cause remains ambiguous at the boundary
between the originating browser/runtime request and the server. No application
code or active record was changed.

Create a new request for browser retesting while preserving Request #1, and
capture the POST `/supplies/requests` request JSON in browser developer tools.
Then compare the new request ID and payload with both its manager display and
read-only database rows. This will distinguish a client/runtime payload issue
from persistence behavior without destructively rewriting evidence.

## Browser-found Accounts area-selection usability fix

Browser verification found that the Worker Regular Area dropdown displayed
occupied areas as though they were available. The frontend now uses the existing
`GET /areas` `assigned_user_id` field and the already-loaded supervisor user list
to keep occupied areas visible but disabled and label them `Assigned to <worker
name>` (falling back to `Assigned` if no matching user is available). Unassigned
areas remain selectable. While editing a worker, that worker's current area
remains enabled because its `assigned_user_id` matches the edited user ID; while
creating a worker or converting a coordinator/supervisor, all occupied areas are
disabled. Backend validation, database constraints, account mutations, and form
styling are unchanged. Changed frontend file is `src/pages/AccountsPage.jsx`;
this checkpoint file was also updated.
Frontend lint, production build, and `git diff --check` pass. Manual browser
reverification confirmed new-worker, existing-worker, and role-conversion area
options.

## Final Supply and Accounts browser verification checkpoint

Manual browser verification is complete for the Worker Supply Request Backend
Integration UI, Coordinator/Supervisor Supply Request Review UI, Supervisor
Supply Request Status Processing UI, and Supervisor Account Management UI.
This final checkpoint supersedes the older pending-browser notes for these
milestones; all four milestones are now browser-verified and complete.

### Manual verification — Supplies

- Worker: the real catalog loads; categories expand and collapse independently
  after the browser-found accordion fix; quantities and request summary track
  the selected item and quantity accurately; submission succeeds with a request
  ID; quantities and summary reset afterward; and the catalog remains usable.
  The Supplies layout also works well at mobile width.
- Data trace: original Request #1 contains unexpected persisted items. Read-only
  investigation confirmed that SQLite, `GET /supplies/requests`, and manager UI
  all agree, but the original POST body was unavailable and root cause could not
  be established. Request #1 is preserved as an unexplained local verification
  artifact and must not be rewritten merely to clean up test data.
- Clean reproduction: browser Network capture for Request #2 showed exactly
  `{area_id: 1, items: [{item_id: 12, quantity: 2}]}`. The backend returned
  `supply_request_id: 2`, and manager review showed Request #2 with exactly that
  one item at quantity 2. The current worker-to-backend-to-database/API-to-manager
  flow is therefore verified.
- Coordinator: worker requests are visible and read-only; Complete/Reopen
  controls are absent.
- Supervisor: status controls are visible; Complete works while retaining the
  request in the list; Reopen works and restores Submitted status.

### Manual verification — Accounts

- Supervisor account creation, name editing, password update, and authentication
  with the new password work.
- Coordinator cannot access Accounts. A deactivated account cannot authenticate;
  reactivation restores login access.
- Role changes work, and changing a role to Worker reveals Regular Area.
- After the browser-found area-option fix, occupied areas remain visible but
  disabled and identify their assigned workers; new or converted workers cannot
  select them; and an existing worker's own current area remains enabled.
- Duplicate-email validation fails cleanly without corrupting either account.
- The Accounts layout works well at mobile width.

### Automated verification versus manual verification

The automated integration checkpoint remains: full backend suite 66 tests, OK;
frontend lint passed; frontend production build passed; and `git diff --check`
passed. The interaction, role-boundary, authentication, responsive-layout, and
end-to-end observations immediately above are manual browser verification, not
automated test claims.

## MVP completion assessment and next action

Repository inspection found no routed core-page placeholder, remaining mock
Supply behavior, or disconnected core API workflow. `PlaceholderPage.jsx` and
its CSS are unused. The worker Dashboard's non-interactive Area Coverage card is
an intentional simple worker view; coordinator/supervisor operational coverage
is connected. Explicitly deferred post-MVP work remains event deletion UI,
supply summaries/filters/timestamps, Snow Log filters/details/pagination/editing/
deletion, a graphical dashboard map, and server-side hardening of worker Snow
Log location scoping. None prevents the established core role workflows from
running.

The core EchoTask MVP is feature-complete. The smallest logical next action is a
stabilization/cleanup/review milestone: review the aggregate dirty-tree diff,
remove only demonstrably unused code after approval, reconcile stale narrative
notes, perform a final role/privacy/accessibility smoke review, and prepare the
changes for human code review without adding features or altering Request #1.

## Portfolio Polish completion checkpoint

The completed **Portfolio Polish** workflow also includes the guarded
`flask seed-portfolio-demo-day` command for refreshing the dedicated
`instance/echotask-portfolio.db`. It requires that exact SQLite database path and
preflights the canonical buildings, areas, users, Snow Log locations, and needed
supply items before making changes. It replaces only demo-day attendance,
assignments, events, supply requests and line items, and Snow Logs; it preserves
the canonical core dataset and supply catalog and refuses to run against the
normal development database. The verified repeatable checkpoint is exactly 22
attendance records, 1 assignment, 1 event, 2 supply requests, and 3 Snow Logs.
The resulting availability checkpoint is 18 Working, 3 Away, and 1 Assigned
elsewhere. The canonical core rows and supply items remain unchanged across the
refresh.

The frontend-only **Portfolio Polish** milestone is complete. On the Attendance
page, coordinators and supervisors now use one combined **Team Availability**
worker list instead of separate Official Attendance and Team Availability
rosters. Each active worker appears once in a native `details`/`summary`
disclosure. Operational availability and official attendance remain visibly and
conceptually separate, including valid combinations such as `Assigned elsewhere`
availability with `Working` or `Away` official attendance. Attendance records
are paired to availability workers by `user_id`; a failed attendance request is
shown as unavailable rather than incorrectly becoming `Not recorded`.

Managers can enter the same list's restrained attendance-management mode with
**Manage attendance**, expand only the worker they need, and reuse the existing
official attendance create/correct, private absence reason, save/cancel, conflict,
and authoritative-refetch behavior. **Done** cancels an active editor and returns
to read mode, and it is disabled during a save. Workers retain their personal
attendance/check-in card followed by shared Team Availability, without other
workers' official attendance, private absence reasons, editing controls, or
manager metadata. Expanded shared details continue to show regular area and all
current assignment destinations/tasks while never rendering assignment notes.

Attendance badges now use consistent semantic colors throughout this combined
UI: `Working` is green, `Away` is amber/orange, `Assigned elsewhere` is blue,
and `Not recorded`, attendance loading, and attendance unavailable states use
muted neutral gray. Native disclosure keyboard behavior, focus-visible styling,
and reduced-motion behavior are unchanged.

The implementation changed only
`Echotask/echotask-frontend/src/pages/AttendancePage.jsx` and
`Echotask/echotask-frontend/src/App.css`. Final frontend lint and production
build pass, and repository-root `git diff --check` passes. No backend source,
API, model, route, database, seed data, or dependency changed for this milestone,
so backend tests were not rerun. No commit or push was performed, and the
aggregate pre-existing dirty worktree remains intentionally available for review.

The final aggregate pre-commit audit found no secrets, committed databases,
generated output, unrelated application changes, or other blocking repository
hygiene issue. Documenting `seed-portfolio-demo-day` in the dedicated portfolio
database workflow and this checkpoint was the audit's final required correction.
The harmless obsolete availability/coverage CSS noted by the audit remains
deliberately deferred to avoid another application-code change before the final
commit.

## Final portfolio stabilization

The project remains feature-complete; no new product milestone was opened.
Repository history confirmed that security-cleanup commit `c6c90b3` replaced
the original workplace CSV rows with generic `Demo Building`, `Demo Area`, and
`Demo Worker` rows. The completed `main` checkpoint restored the UofM building
names but used rewritten area labels and newly fictional worker names. This
correction restores the exact areas, descriptions, worker names, and ID-based
worker assignments supplied in commit `b98ca96`. Existing SQLite databases do
not update automatically when CSV files change and therefore required reseeding.

The canonical `seed-core-data` path uses the exact supplied UofM workplace data
from repository history: 10 buildings, 22 operational areas, the 22 supplied
worker names with one permanent worker per area, and coordinator/supervisor
accounts without permanent areas. Generic `Demo Building NN` / `Demo Worker NN`
entities and the obsolete `seed-core-demo` command must not be used by normal
setup. Reproducible public Worker, Coordinator, and Supervisor credentials,
complete installation/runtime prerequisites, SQLite requirements, Windows and
macOS/Linux setup, and the absence of required editor/browser extensions are
documented in the repository README, exist only so portfolio reviewers can
authenticate; they do not authorize replacing the supplied workplace data with
generated dummy entities in any future milestone.

The existing ignored database backup was preserved. The pre-correction
portfolio database was additionally preserved as
`instance/echotask-portfolio-before-supplied-data-restoration-20260818.db`.
Both active local databases were rebuilt with the canonical seed. Verification
found 10 buildings, 22 areas, 22
workers, 22 permanent worker-area assignments, one coordinator, one supervisor,
and no generic demo building or worker rows. The documented Worker, Coordinator,
and Supervisor accounts all authenticated successfully. The documented setup
sequence also succeeded against a fresh isolated SQLite database. The full
backend suite passes (69 tests), frontend dependency installation, lint, and
production build pass, and repository hygiene checks pass.

## Next action

No feature work is planned. Preserve this final portfolio stabilization state
for human review; do not open another milestone, commit, or push unless
explicitly requested.
