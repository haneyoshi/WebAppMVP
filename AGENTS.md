# Repository working instructions

## User interaction

- Prefer doing technical work directly instead of asking the user to do it manually.
- Before asking the user to run a command, inspect files, search code, test an API,
  inspect logs, or perform another technical check, first determine whether Codex
  can perform it directly.
- Use repository inspection, terminal commands, automated tests, focused scripts,
  API calls, and code searches whenever practical.
- Reserve manual user testing mainly for visual appearance, usability, browser
  interaction, or behavior that cannot be judged reliably through automated
  inspection.
- When manual user action is genuinely necessary, request one clear next step at a
  time and briefly explain why it is needed.
- Do not give the user long batches of commands unless explicitly requested.

## Output discipline

- Do not ask the user to copy and paste large terminal outputs; inspect output
  directly whenever possible.
- If user input is necessary, narrow the command so it produces only the specific
  information needed. Prefer a screenshot or short exact result to a large terminal
  dump.
- Keep completion reports concise and focused on decisions, changes, verification
  results, blockers, and next actions.

## Testing discipline

- Choose verification in proportion to the files and behavior changed.
- Do not repeatedly rerun checks that have already passed unless relevant code has
  changed.
- For frontend-only EchoTask milestones, normally run `npm run lint` and
  `npm run build` from `Echotask/echotask-frontend`, plus `git diff --check` from
  the repository root.
- Do not rerun the full backend test suite during frontend-only work.
- Run backend tests when backend code, configuration, dependencies, database
  behavior, or API behavior changes. Start with the smallest relevant test scope.
- Prefer focused smoke tests over unnecessarily broad manual testing.

## Project context

- Treat repository-root `PROJECT_CONTEXT.md` as the primary source of truth for
  the current branch and checkpoint, completed milestones, next action, product
  decisions, API contracts, and project-specific verification rules.
- Read `PROJECT_CONTEXT.md` before making implementation decisions or proposing
  the next milestone.
- Keep this file focused on durable working behavior. Keep changing milestone and
  checkpoint information in `PROJECT_CONTEXT.md` rather than duplicating it here.

## Scope discipline

- Follow the smallest milestone described in `PROJECT_CONTEXT.md`.
- Do not expand EchoTask into unnecessary abstractions or features. Prefer simple
  MVP implementations over speculative scalability.
- Do not introduce individual task or work-order management unless explicitly
  requested.
- When a requirement is ambiguous and implementation would materially expand
  scope, report the issue instead of silently inventing a larger solution.

## Git discipline

- Do not commit, push, merge, switch branches, or rewrite history unless explicitly
  instructed.
- After implementation, leave changes available for review.
- Clearly report `git status` at the end of implementation work when relevant.
