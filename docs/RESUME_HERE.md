# Resume Here — StockPilot AI

## Start here

Read `README.md`, `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `ARCHITECTURE.md`, then inspect the actual repository and `git status`. Do not assume this document is more current than source code.

## Current state

- Managed Webdev project directory: `/home/ubuntu/stockpilot`.
- Branch: `main`.
- Phase 1 foundation is complete. Phase 2 identity/tenancy is in progress.
- The requested GitHub repository transition was declined; the managed repository remains canonical. Do not reopen the transfer unless the user explicitly asks.
- Server/database capabilities are enabled; frontend Preview runtime is port 3000.

## What works

The backend serves `/api/v1/health/` and OpenAPI routes. Identity models and migrations exist for organizations, memberships, invitations, profiles, and audit events. Registration transactionally creates an owner organization, JWT email-compatible login returns access/refresh tokens, refresh/logout/me routes exist, token blacklist support is installed, and `GET /api/v1/organizations/` returns only the authenticated user's active memberships. Four backend tests pass, including tenant isolation. The frontend has the polished landing page and responsive shell with route manifest and empty states; its typecheck, lint, two tests, and production build pass.

## Exact next task

Finish Phase 2: password recovery/reset, organization switching, invitations and membership administration, explicit role permission endpoints/tests, and rate limiting for authentication/sensitive endpoints. Then implement Phase 3 normalized categories/products/hubs/suppliers and read-only inventory views before transactional stock services.

## Commands/checks

From root: `pnpm install --frozen-lockfile`. Frontend: `pnpm --dir frontend typecheck && pnpm --dir frontend lint && pnpm --dir frontend test && pnpm --dir frontend build`. Backend: `cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/pytest -q -rs`. Preview: `pnpm --dir frontend dev` and verify `/manus-routes.json`.

## Known blockers

No Supabase, Upstash, or Groq credentials are available. Keep external adapters configurable and make missing integrations fail explicitly without breaking core tests. No deployment URL is verified. Production PostgreSQL integration still needs a Supabase DSN; local unsupported-DSN checks use SQLite.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
