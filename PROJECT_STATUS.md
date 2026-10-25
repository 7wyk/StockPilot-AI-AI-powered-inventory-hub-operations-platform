# StockPilot AI — Project Status

## Current phase
Phase 3 — Core inventory, in progress.

## Phase status
- Phase 0 — `DONE`: repository inspection, design, continuity documents.
- Phase 1 — `DONE`: monorepo foundation, Django health/OpenAPI, responsive Vite shell, CI, and first checks.
- Phase 2 — `IN_PROGRESS`: organization, membership, role, profile, audit models and migrations; JWT registration/login/refresh/logout/me; tenant-scoped organization listing; identity/tenant tests. Password recovery, invitation/team administration, organization switching, and full role matrix enforcement remain.
- Phase 3 — `IN_PROGRESS`: categories, products, hubs, suppliers, authoritative balances, immutable stock movements, tenant-scoped APIs, dashboard summary, idempotent transactional receipt/issue/adjustment service, and inventory tests are implemented. Supplier workflows, richer filters, and frontend data wiring remain.
- Phase 4 — `TODO`: restock and transfer lifecycle.
- Phase 5 — `IN_PROGRESS`: public landing page and responsive shell/empty states are implemented; live workflows remain.
- Phase 6 — `TODO`: analytics, reports, exports, and storage.
- Phase 7 — `TODO`: Groq assistant, controlled tools, confirmation flow, history, memory.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features

The managed Webdev project is at `/home/ubuntu/stockpilot` with server/database capabilities enabled and Preview runtime port 3000. The root pnpm workspace has a reviewed `allowBuilds` policy for esbuild and one lockfile.

The backend includes organization, membership, invitation, profile, and audit models; SimpleJWT access/refresh configuration with blacklist support; transactional registration; email-compatible login; refresh, logout, and current-user endpoints; and tenant-scoped organization listing. The core inventory domain now includes organization-scoped categories, products with SKU/pricing/reorder fields, hubs, suppliers and supplier-product links, product/hub balances, immutable signed stock movements, query-scoped API viewsets, dashboard metrics, idempotency keys, row locking, negative-stock protection, available-stock validation, and audit events for stock changes.

The frontend landing page and responsive shell remain available with honest empty states for the domain screens. CI, environment, deployment, security, architecture, plan, TODO, decisions, and resume documents are present.

## Tests actually run

- Foundation backend: Django check and health test passed.
- Foundation frontend: typecheck, lint, 2 Vitest tests, production build, route manifest, and landing HTML response passed.
- Phase 2 backend: 4 tests passed.
- Phase 3 backend: `cd backend && ../.venv/bin/python manage.py makemigrations --check --dry-run` reported no changes; `../.venv/bin/pytest -q -rs` passed 7 tests; Django check passed.

## Git state

- Branch: `main`.
- Phase 1 foundation commit: `a71c7025b2f04232520b11f2912a23b473210d86`.
- Phase 2 identity milestone commit: `f666781bfd428c7e05c38a691905f7954c96094d`.
- Phase 3 core inventory milestone commit: `e073facbf234de720a4b56c7ebc198ea16011e1e`.
- This status update will be recorded in the next documentation checkpoint.
- The requested GitHub repository is empty; the canonical-transfer confirmation was declined. The managed repository remains canonical, and no plain GitHub push was attempted.

## Known bugs and limitations

Password recovery, invitation/team administration, organization switching, full role matrix enforcement, restock/transfer lifecycles, frontend API auth/data wiring, reports, AI, and external service adapters are not complete. The host-provided `DATABASE_URL` is MySQL; unsupported non-PostgreSQL DSNs intentionally fall back to SQLite for local checks, while production documentation targets Supabase PostgreSQL. No production credentials or live deployment are configured or verified.

## Exact next task

Implement Phase 4 restock requests and inter-hub transfers with explicit lifecycle states, permission checks, source-availability validation, idempotent dispatch/receipt operations, movement/audit records, and backend tests. In parallel, complete the remaining Phase 2 invitation/role gaps before exposing mutation controls in the frontend.
