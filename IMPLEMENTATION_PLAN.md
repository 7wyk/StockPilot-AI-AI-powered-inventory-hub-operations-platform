# StockPilot AI — Implementation Plan

Statuses: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

## Phase 0 — Repository inspection and planning — DONE

The managed project was initialized, the empty requested GitHub repository was inspected, and the architecture/design, acceptance TODO, status, decisions, and resume documents were created. The `Electric signal` visual direction was chosen for a bright, precise operations workspace.

## Phase 1 — Foundation — DONE

The repository contains a frontend/backend monorepo, environment examples, pnpm workspace policy and lockfile, lint/format/typecheck/test commands, Django settings and API structure, an unauthenticated health/readiness endpoint, OpenAPI documentation routes, route manifest, accessible frontend shell, CI, and initial tests. Verification completed: Django check and health test passed; frontend typecheck, lint, two Vitest tests, and Vite production build passed; the dev server served the route manifest and landing HTML.

## Phase 2 — Database and identity — DONE

Organization, membership, invitation, profile, and audit models with Django migrations; JWT registration/login/refresh/logout/me; refresh-token blacklist support; email-compatible login; tenant-scoped organization listing; active-membership resolver; member and invitation administration; secure invitation acceptance; membership audit events; role-permission matrix endpoint; configurable authentication and sensitive-endpoint throttles; action-level permission enforcement across domain viewsets; identity/tenant tests. Password recovery/reset and owner-transfer policy are deferred to a future milestone.

Dependencies: Phase 1. Verification: 18 backend tests pass.

## Phase 3 — Core inventory — DONE

Normalized organization-scoped categories, products, hubs, suppliers and supplier-product links; product/hub balances with database constraints; immutable signed stock movements; tenant-scoped DRF APIs; dashboard summary; idempotency keys; row locking; receipt/issue/adjustment validation; negative/available-stock protection; audit records; migrations; inventory tests.

Dependencies: Phase 2. Verification: migration drift check, Django check, and inventory tests pass.

## Phase 4 — Restocking and transfers — DONE

Restock request state transitions `draft → pending → approved → ordered → received`, cancellation before receipt, inter-hub transfer transitions `draft → pending → approved → dispatched → received`, cancellation before dispatch, role gates, membership checks, source availability validation, row locks, idempotent restock receipt/source dispatch/destination receipt effects, immutable movement/audit records, migrations, lifecycle tests.

Dependencies: Phases 2–3. Verification: lifecycle, insufficient-stock, idempotency, migration, and authorization checks pass.

## Phase 5 — Frontend application — DONE

Public landing page and responsive workspace shell with polished navigation, dashboard empty states, AI assistant entry, route manifest, reduced-motion support, responsive behavior, login/registration UI, typed JWT API client with refresh/logout handling, live Overview summary query, permission-aware Team page wired to member/invitation/permission APIs. Inventory, Categories, Hubs, Suppliers, Restock, and Transfers have confirmation-driven React Hook Form + Zod mutations backed by typed Django APIs, permission-aware controls, state-machine transition visibility, backend error feedback, and TanStack Query refreshes.

Dependencies: Phases 2–4. Verification: frontend typecheck, ESLint, 7 Vitest tests, production build pass.

## Manus handoff checkpoint — COMPLETE

Feature development stopped at the Manus workspace. Complete verified source committed on `main` at `be28094b655833256f9d2451ff189d12dd7b2166`.

## Phase 6 — Analytics and reports — DONE

Deterministic risk, low-stock, stockout, valuation, slow/excess, movement, imbalance calculations. Report metadata model. CSV/PDF exports via ReportLab. Configurable storage adapter (local filesystem + Supabase Storage ready). Frontend Reports page with Recharts for inventory value trend, movement trend, inventory by hub bar chart, and low-stock table. Export download controls.

Dependencies: Phases 2–4. Verification: analytics calculation tests, export tests, permission tests, tenant isolation tests pass. Commit: `5396f823744bdbd7585cf908120b6130c0eb2a1f`.

## Phase 7 — AI assistant — DONE

Groq adapter with deterministic rule-based offline fallback. Persistent conversation and message models with tenant-scoped foreign keys. 9 read tools: `get_inventory_summary`, `get_low_stock_products`, `get_out_of_stock_products`, `get_hub_inventory`, `search_products`, `get_recent_movements`, `get_restock_requests`, `get_transfer_requests`, `get_supplier_list`. 5 write confirmation tools: `receive_stock`, `issue_stock`, `adjust_stock`, `create_transfer`, `create_restock_request`. All tools enforce tenant scope via active membership. Write tools return structured confirmation proposals (`requires_confirmation: true`). Confirmed actions execute through `/api/v1/ai/confirm-action/` which re-validates permissions and delegates to existing transactional services with audit logging. User preferences/memory model. Polished React chat UI at `/app/assistant` with persistent conversation sidebar, active chat history, tool execution indicators, interactive confirmation cards with Confirm/Cancel, and user preferences drawer.

Dependencies: Phases 2–6. Verification: 48 backend tests (conversation tenant isolation, user permissions, read tool correctness, write confirmation requirement, confirmed transaction execution, audit logging, cross-tenant ID rejection, invalid argument rejections, scoped user preferences). Frontend tests pass. TypeScript + Vite production build pass.

## Phase 8 — Performance and reliability — TODO

Add Upstash Redis caching/rate limiting/coordination, idempotent Celery tasks, query optimization, retry/timeouts, structured logs, and outage fallbacks. Verify that caching never crosses scopes and that Redis/Celery failures do not corrupt inventory.

Dependencies: Phases 3–7. Verification: focused cache invalidation, task, rate-limit, and degraded-service tests.

## Phase 9 — QA and security — TODO

Run backend/frontend suites, formatting/linting, type checks, dependency/security checks, and critical-flow verification. Fix high-priority issues and document genuine external blockers.

Dependencies: Phases 1–8. Verification: all available checks pass or are explicitly documented with cause and scope.

## Phase 10 — Deployment readiness and handoff — TODO

Finalize Vercel, Render API/worker, Supabase, Upstash, Groq configuration, migrations, health checks, demo seed instructions, recruiter walkthrough, status, decisions, and resume handoff. Only report deployments or URLs actually confirmed by provider responses.

Dependencies: Phases 1–9. Verification: production build/start configuration, docs review, safe demo seed, and final continuity audit.
