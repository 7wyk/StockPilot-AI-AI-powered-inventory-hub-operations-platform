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

The core inventory backend has categories, products, hubs, suppliers, supplier-product links, product/hub balances, immutable signed stock movements, tenant-scoped APIs, dashboard summary metrics, idempotent stock receipt/issue/adjustment operations, row locking, negative/available-stock protections, and audit records. Restock and transfer APIs implement row-locked lifecycle transitions with permission gates and idempotent movement effects. Organization administration includes tenant-scoped member listing, role changes, removal, invitation lifecycle, secure token acceptance, membership reactivation, and a server-authoritative role-permission matrix. Authentication and invitation acceptance use configurable cache-backed throttles, and domain viewsets enforce action-level permissions. The full backend suite passes 18 tests, including role enforcement, throttling, and tenant isolation. The frontend Team page at `/app/team` is wired to live member, invitation, and permission APIs, with permission-aware controls and confirmations for consequential access changes. Inventory, Categories, Hubs, Suppliers, Restock, and Transfers now have live React Hook Form + Zod mutation dialogs, typed API calls, server-permission UX, state-machine action controls, confirmation reviews, error feedback, and query refreshes. Stock forms never calculate authoritative balances client-side. Supplier-product relationship editing is intentionally unavailable because the existing backend only exposes read-only nested links. Frontend typecheck, lint, 7 tests, and production build pass. The local API health endpoint is verified. The mutation checkpoint is `5180c11c2a39728aa7c5f505b7d26fdb5a380edc`.

## Exact next task

Begin Phase 6 analytics and reports: deterministic tenant-scoped risk/valuation/movement calculations, CSV/PDF exports, secure file handling, and export tests. Keep integrations explicit and do not mark provider-dependent storage complete without credentials.

## Commands/checks

From root: `pnpm install --frozen-lockfile`. Frontend: `pnpm --dir frontend typecheck && pnpm --dir frontend lint && pnpm --dir frontend test && pnpm --dir frontend build`. Backend: `cd backend && ../.venv/bin/python manage.py check && ../.venv/bin/pytest -q -rs`. Preview: `pnpm --dir frontend dev` and verify `/manus-routes.json`.

## Known blockers

No Supabase, Upstash, or Groq credentials are available. Keep external adapters configurable and make missing integrations fail explicitly without breaking core tests. No deployment URL is verified. Production PostgreSQL integration still needs a Supabase DSN; local unsupported-DSN checks use SQLite.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
