# Resume Here — StockPilot AI

## Start here

Read `README.md`, `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `ARCHITECTURE.md`, then inspect the actual repository and `git status`. Do not assume this document is more current than source code.

## Current state

- Managed Webdev project directory: `/home/ubuntu/stockpilot`.
- Branch: `main`; Phase 1 foundation, Phase 2 identity foundation, Phase 3 core inventory, and Phase 4 workflow milestones are committed.
- The requested GitHub repository transition was declined; the managed repository remains canonical. Do not reopen the transfer unless the user explicitly asks.
- Server/database capabilities are enabled; frontend Preview runtime is port 3000.

## What works

The backend serves health and OpenAPI routes. Identity models and migrations exist for organizations, memberships, invitations, profiles, and audit events. Registration transactionally creates an owner organization, JWT email-compatible login returns access/refresh tokens, refresh/logout/me routes exist, token blacklist support is installed, organization listing is tenant-scoped, and a member can switch the profile-selected active organization only to another membership they own.

The core inventory backend has categories, products, hubs, suppliers, supplier-product links, product/hub balances, immutable signed stock movements, tenant-scoped APIs, dashboard summary metrics, idempotent stock receipt/issue/adjustment operations, row locking, negative/available-stock protections, and audit records. Restock and transfer APIs implement row-locked lifecycle transitions with permission gates and idempotent movement effects. Ten backend tests pass. The frontend has the polished landing page and responsive shell with route manifest and empty states. A typed API client supports JWT persistence, refresh, registration/login/logout, Overview dashboard metrics, and tenant-scoped Inventory/Hubs/Restock/Transfers list queries. Its typecheck, lint, three tests, and production build pass. The local API health endpoint is verified.

## Exact next task

Finish remaining Phase 2 authorization work: invitations/membership administration, explicit role permission tests, and authentication rate limiting. Then add confirmation-driven create/mutation forms for products, hubs, transfers, and restock requests.

## Commands/checks

From root: `pnpm install --frozen-lockfile`. Frontend: `pnpm --dir frontend typecheck && pnpm --dir frontend lint && pnpm --dir frontend test && pnpm --dir frontend build`. Backend: `cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/pytest -q -rs`. Preview: `pnpm --dir frontend dev` and verify `/manus-routes.json`.

## Known blockers

No Supabase, Upstash, or Groq credentials are available. Keep external adapters configurable and make missing integrations fail explicitly without breaking core tests. No deployment URL is verified. Production PostgreSQL integration still needs a Supabase DSN; local unsupported-DSN checks use SQLite.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
