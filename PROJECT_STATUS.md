# StockPilot AI — Project Status

## Current phase
Phase 5 — Frontend application, in progress.

## Phase status
- Phase 0 — `DONE`: repository inspection, design, continuity documents.
- Phase 1 — `DONE`: monorepo foundation, Django health/OpenAPI, responsive Vite shell, CI, and first checks.
- Phase 2 — `IN_PROGRESS`: organization, membership, role, profile, audit models and migrations; JWT registration/login/refresh/logout/me; tenant-scoped organization listing; active organization switching; invitation/member administration; an explicit server-authoritative role matrix; configurable authentication/sensitive-endpoint throttles; and action-level domain endpoint enforcement. Password recovery, broader audit coverage, and owner-transfer policy remain.
- Phase 3 — `IN_PROGRESS`: categories, products, hubs, suppliers, balances, immutable stock movements, tenant-scoped APIs, dashboard summary, idempotent transactional receipt/issue/adjustment service, and inventory tests are implemented. Supplier workflows, richer filters, and frontend data wiring remain.
- Phase 4 — `IN_PROGRESS`: restock request and inter-hub transfer state machines are implemented with permission gates, membership checks, availability validation, idempotent stock effects, movement/audit records, migrations, and lifecycle tests. More granular role policy, cancellation/refund semantics, and frontend wiring remain.
- Phase 5 — `IN_PROGRESS`: public landing page, responsive shell, login/registration form, typed auth client, refresh/logout handling, route manifest, Overview live dashboard summary query, and permission-aware Team administration page are implemented. Inventory/Hub/Restock/Transfer route data lists are wired to the tenant-scoped API; domain create/mutation forms remain intentionally disabled until their confirmation UI is connected.
- Phase 6 — `TODO`: analytics, reports, exports, and storage.
- Phase 7 — `TODO`: Groq assistant, controlled tools, confirmation flow, history, memory.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features

The managed Webdev project is at `/home/ubuntu/stockpilot` with server/database capabilities enabled and Preview runtime port 3000. The root pnpm workspace has a reviewed `allowBuilds` policy for esbuild and one lockfile.

The backend includes organization, membership, invitation, profile, and audit models; JWT access/refresh configuration with blacklist support; transactional registration; email-compatible login; refresh, logout, and current-user endpoints; tenant-scoped organization listing; and a server-authoritative role permission matrix. Organization administration supports member listing, role changes, member removal, invitation creation/status/cancellation/resend, secure tokenized acceptance, membership reactivation, and audit events for invitation and membership actions. Registration, login, refresh, logout, and invitation acceptance use configurable cache-backed throttles. Domain viewsets enforce explicit permissions per read, create, edit, archive, approval, dispatch, receipt, and stock-adjustment action. Owner transfer remains intentionally out of scope for this milestone.

The core inventory domain includes organization-scoped categories, products with SKU/pricing/reorder fields, hubs, suppliers and supplier-product links, product/hub balances, immutable signed stock movements, query-scoped API viewsets, dashboard metrics, idempotency keys, row locking, negative-stock protection, available-stock validation, and audit events for stock changes.

Operational workflows now include restock requests (`draft → pending → approved → ordered → received`, with cancellation before receipt) and inter-hub transfers (`draft → pending → approved → dispatched → received`, with cancellation before dispatch). Transfer dispatch applies an idempotent source `transfer_out`; receipt applies an idempotent destination `transfer_in`; restock receipt applies an idempotent `receipt`. State transitions are row-locked and auditable.

The frontend landing page and responsive shell remain available with honest empty states for the domain screens. The sidebar workspace switcher loads the authenticated user’s active organization and can switch only among memberships. A typed API client persists JWT tokens, refreshes access tokens on 401, supports registration/login/logout, queries the organization-scoped dashboard summary, and exposes member/invitation/permission mutations. Overview renders sign-in, loading, error, and live metric states instead of fabricated KPI values. The Team page at `/app/team` loads live members, pending invitations, and the server permission matrix; it conditionally exposes invite, role, remove, resend, and cancel controls and confirms consequential actions before calling the API. Inventory, Hubs, Restock, and Transfers render sign-in/loading/error/empty/table states against their real list endpoints, with unavailable create buttons labeled as next. The local Django API responds healthy on `/api/v1/health/` and serves OpenAPI YAML on `/api/v1/schema/`. CI, environment, deployment, security, architecture, plan, TODO, decisions, and resume documents are present.

## Tests actually run

- Foundation backend: Django check and health test passed.
- Foundation frontend: typecheck, lint, 2 Vitest tests, production build, route manifest, and landing HTML response passed.
- Phase 2 + 3 + 4 backend: migration drift checks reported no changes; `cd backend && ../.venv/bin/pytest -q -rs` passed 11 tests; Django check passed.
- Organization administration milestone: migration drift check, Django check, and `cd backend && ../.venv/bin/pytest -q -rs` passed 15 tests, including invitation lifecycle, role enforcement, member removal, audit behavior, and tenant isolation.
- Authorization hardening milestone: Django check and `cd backend && ../.venv/bin/pytest -q -rs` passed 18 tests, including IP-based registration throttling, action-level role enforcement, known-ID object isolation, invitation lifecycle, and tenant isolation.
- Team administration milestone: frontend typecheck, lint, 3 Vitest tests, and production build passed; `/app/team` is included in `frontend/public/manus-routes.json`.
- Frontend integration: typecheck, lint, 3 Vitest tests, and production build passed; `/manus-routes.json` includes `/login` and the local API health endpoint returned `{ "status": "ok", "database": "ok" }`.

## Git state

- Branch: `main`.
- Phase 1 foundation commit: `a71c7025b2f04232520b11f2912a23b473210d86`.
- Phase 2 identity milestone commit: `f666781bfd428c7e05c38a691905f7954c96094d`.
- Phase 3 core inventory milestone commit: `e073facbf234de720a4b56c7ebc198ea16011e1e`.
- Phase 4 workflow milestone commit: `bac38eebaa081493957a9df350282e5a0abec204`.
- Frontend auth/live metrics commit: `841afcc2d058f1ec90177b657f40883406602cc8`.
- Frontend live resource lists commit: `a62f6e4b8ac192c720ccbed66f4d297eec82ac37`.
- Organization workspace switcher commit: `4acdd0456822c104badf06620937149aca9f33b9`.
- Active organization switch commit: `ae85d4c33a6a26bbde7af6a2146bee58d7783f89`.
- This status update will be recorded in the next documentation checkpoint.
- The requested GitHub repository was reconnected and restored at checkpoint `825afde`; this workspace is now tracking its `main` branch.

## Known bugs and limitations

Password recovery, broader audit coverage, owner transfer, supplier procurement flows, frontend team administration and mutation forms, reports, AI, and external service adapters are not complete. Throttles currently use Django's disposable cache and should move to tenant-safe Upstash coordination in the reliability milestone. The host-provided `DATABASE_URL` is MySQL; unsupported non-PostgreSQL DSNs intentionally fall back to SQLite for local checks, while production documentation targets Supabase PostgreSQL. No production credentials or live deployment are configured or verified.

## Exact next task

Add confirmation-driven create/mutation forms for products, categories, hubs, suppliers, stock adjustments, restock requests, and transfers. Keep all unavailable actions clearly labeled rather than silently mutating.
