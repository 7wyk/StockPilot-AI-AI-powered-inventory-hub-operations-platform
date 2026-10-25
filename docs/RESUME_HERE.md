# Resume Here — StockPilot AI

## Start here

Read `README.md`, `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `ARCHITECTURE.md`, then inspect the actual repository and `git status`. Do not assume this document is more current than source code.

## Current state

- Managed Webdev project directory: `/home/ubuntu/stockpilot`.
- Branch: `main`.
- Phase 0 planning and the Phase 1 foundation milestone are complete in the current working tree; the next task is Phase 2 identity and tenancy.
- The requested GitHub repository is empty; the active canonical repository is still Managed by Manus.
- Server and managed database capabilities are enabled; the frontend dev server is available on port 3000 during this session.

## What works

The backend runs Django checks and serves `/api/v1/health/`. The first backend health test passes. The frontend has a real Vite/React landing page and responsive workspace shell with honest empty states for Overview, Inventory, Hubs, Transfers, Reports, Activity, Settings, and AI Assistant. The route manifest is served at `/manus-routes.json`. Frontend typecheck, lint, tests (2), and production build pass.

## Exact next task

Implement organizations, memberships, roles, permission classes, JWT access/refresh endpoints, protected route foundations, and tenant-isolation tests. Keep the requested production boundary: Supabase PostgreSQL when `DATABASE_URL` is a PostgreSQL DSN; local SQLite fallback only for unsupported/missing DSNs during local checks.

## Commands/checks

From the repository root: `pnpm install --frozen-lockfile`. Frontend: `pnpm --dir frontend typecheck && pnpm --dir frontend lint && pnpm --dir frontend test && pnpm --dir frontend build`. Backend: `cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/pytest -q -rs`. Preview: `pnpm --dir frontend dev` and verify `/manus-routes.json`.

## Known blockers

No Supabase, Upstash, or Groq credentials are available in this session. Keep adapters configurable and make missing integrations fail explicitly without breaking core health/tests. No deployment URL is verified. Connecting the project to the requested GitHub repository requires the platform's owner-confirmed canonical-transfer flow.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
