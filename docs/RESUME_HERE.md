# Resume Here — StockPilot AI

## Start here

Read `README.md`, `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `ARCHITECTURE.md`, then inspect the actual repository and `git status`. Do not assume this document is more current than source code.

## Current state

- Managed Webdev project directory: `/home/ubuntu/stockpilot`.
- Branch: `main`; Phase 1 foundation, Phase 2 identity foundation, and the Phase 3 core inventory milestone are committed.
- The requested GitHub repository transition was declined; the managed repository remains canonical. Do not reopen the transfer unless the user explicitly asks.
- Server/database capabilities are enabled; frontend Preview runtime is port 3000.

## What works

The backend serves health and OpenAPI routes. Identity models and migrations exist for organizations, memberships, invitations, profiles, and audit events. Registration transactionally creates an owner organization, JWT email-compatible login returns access/refresh tokens, refresh/logout/me routes exist, token blacklist support is installed, and organization listing is tenant-scoped.

The core inventory backend now has categories, products, hubs, suppliers, supplier-product links, product/hub balances, immutable signed stock movements, tenant-scoped list/detail APIs, dashboard summary metrics, idempotent stock receipt/issue/adjustment operations, row locking, negative/available-stock protections, and audit records. Seven backend tests pass. The frontend has the polished landing page and responsive shell with route manifest and empty states; its typecheck, lint, two tests, and production build pass.

## Exact next task

Implement Phase 4 restock requests and inter-hub transfers with explicit lifecycle states, permission checks, source-availability validation, idempotent dispatch/receipt operations, movement/audit records, and backend tests. Then finish Phase 2 invitation/role gaps and wire the frontend to authenticated API data before exposing mutation controls.

## Commands/checks

From root: `pnpm install --frozen-lockfile`. Frontend: `pnpm --dir frontend typecheck && pnpm --dir frontend lint && pnpm --dir frontend test && pnpm --dir frontend build`. Backend: `cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/pytest -q -rs`. Preview: `pnpm --dir frontend dev` and verify `/manus-routes.json`.

## Known blockers

No Supabase, Upstash, or Groq credentials are available. Keep external adapters configurable and make missing integrations fail explicitly without breaking core tests. No deployment URL is verified. Production PostgreSQL integration still needs a Supabase DSN; local unsupported-DSN checks use SQLite.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
