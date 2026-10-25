# StockPilot AI — Project Status

## Current phase
Phase 4 — Restock and transfer workflows, in progress.

## Phase status
- Phase 0 — `DONE`: repository inspection, design, continuity documents.
- Phase 1 — `DONE`: monorepo foundation, Django health/OpenAPI, responsive Vite shell, CI, and first checks.
- Phase 2 — `IN_PROGRESS`: organization, membership, role, profile, audit models and migrations; JWT registration/login/refresh/logout/me; tenant-scoped organization listing; identity/tenant tests. Password recovery, invitation/team administration, organization switching, and full role matrix enforcement remain.
- Phase 3 — `IN_PROGRESS`: categories, products, hubs, suppliers, balances, immutable stock movements, tenant-scoped APIs, dashboard summary, idempotent transactional receipt/issue/adjustment service, and inventory tests are implemented. Supplier workflows, richer filters, and frontend data wiring remain.
- Phase 4 — `IN_PROGRESS`: restock request and inter-hub transfer state machines are implemented with permission gates, membership checks, availability validation, idempotent stock effects, movement/audit records, migrations, and lifecycle tests. More granular role policy, cancellation/refund semantics, and frontend wiring remain.
- Phase 5 — `IN_PROGRESS`: public landing page and responsive shell/empty states are implemented; live workflows remain.
- Phase 6 — `TODO`: analytics, reports, exports, and storage.
- Phase 7 — `TODO`: Groq assistant, controlled tools, confirmation flow, history, memory.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features

The managed Webdev project is at `/home/ubuntu/stockpilot` with server/database capabilities enabled and Preview runtime port 3000. The root pnpm workspace has a reviewed `allowBuilds` policy for esbuild and one lockfile.

The backend includes organization, membership, invitation, profile, and audit models; JWT access/refresh configuration with blacklist support; transactional registration; email-compatible login; refresh, logout, and current-user endpoints; and tenant-scoped organization listing.

The core inventory domain includes organization-scoped categories, products with SKU/pricing/reorder fields, hubs, suppliers and supplier-product links, product/hub balances, immutable signed stock movements, query-scoped API viewsets, dashboard metrics, idempotency keys, row locking, negative-stock protection, available-stock validation, and audit events for stock changes.

Operational workflows now include restock requests (`draft → pending → approved → ordered → received`, with cancellation before receipt) and inter-hub transfers (`draft → pending → approved → dispatched → received`, with cancellation before dispatch). Transfer dispatch applies an idempotent source `transfer_out`; receipt applies an idempotent destination `transfer_in`; restock receipt applies an idempotent `receipt`. State transitions are row-locked and auditable.

The frontend landing page and responsive shell remain available with honest empty states for the domain screens. CI, environment, deployment, security, architecture, plan, TODO, decisions, and resume documents are present.

## Tests actually run

- Foundation backend: Django check and health test passed.
- Foundation frontend: typecheck, lint, 2 Vitest tests, production build, route manifest, and landing HTML response passed.
- Phase 2 + 3 + 4 backend: migration drift checks reported no changes; `cd backend && ../.venv/bin/pytest -q -rs` passed 10 tests; Django check passed.

## Git state

- Branch: `main`.
- Phase 1 foundation commit: `a71c7025b2f04232520b11f2912a23b473210d86`.
- Phase 2 identity milestone commit: `f666781bfd428c7e05c38a691905f7954c96094d`.
- Phase 3 core inventory milestone commit: `e073facbf234de720a4b56c7ebc198ea16011e1e`.
- Phase 4 workflow milestone commit: `bac38eebaa081493957a9df350282e5a0abec204`.
- This status update will be recorded in the next documentation checkpoint.
- The requested GitHub repository is empty; the canonical-transfer confirmation was declined. The managed repository remains canonical, and no plain GitHub push was attempted.

## Known bugs and limitations

Password recovery, invitation/team administration, organization switching, full role matrix enforcement, supplier procurement flows, frontend API auth/data wiring, reports, AI, and external service adapters are not complete. The host-provided `DATABASE_URL` is MySQL; unsupported non-PostgreSQL DSNs intentionally fall back to SQLite for local checks, while production documentation targets Supabase PostgreSQL. No production credentials or live deployment are configured or verified.

## Exact next task

Finish the remaining Phase 2 authorization surface and begin frontend data wiring: organization switch/profile context, invitation/membership administration, explicit role permission tests, auth rate limiting, and a small authenticated API client. Then connect Overview, Products, Hubs, Transfers, and Restock screens to the real endpoints without introducing mutation controls that lack confirmation/error states.
