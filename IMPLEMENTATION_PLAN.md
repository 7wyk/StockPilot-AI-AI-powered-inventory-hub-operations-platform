# StockPilot AI — Implementation Plan

Statuses: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

## Phase 0 — Repository inspection and planning — DONE

The managed project was initialized, the empty requested GitHub repository was inspected, and the architecture/design, acceptance TODO, status, decisions, and resume documents were created. The `Electric signal` visual direction was chosen for a bright, precise operations workspace.

## Phase 1 — Foundation — DONE

The repository contains a frontend/backend monorepo, environment examples, pnpm workspace policy and lockfile, lint/format/typecheck/test commands, Django settings and API structure, an unauthenticated health/readiness endpoint, OpenAPI documentation routes, route manifest, accessible frontend shell, CI, and initial tests. Verification completed: Django check and health test passed; frontend typecheck, lint, two Vitest tests, and Vite production build passed; the dev server served the route manifest and landing HTML.

## Phase 2 — Database and identity — IN_PROGRESS

Implemented so far: organization, membership, invitation, profile, and audit models with Django migrations; JWT registration/login/refresh/logout/me; refresh-token blacklist support; email-compatible login; tenant-scoped organization listing; active-membership resolver; member and invitation administration; secure invitation acceptance; membership audit events; an explicit role-permission matrix endpoint; configurable authentication and sensitive-endpoint throttles; action-level permission enforcement across domain viewsets; and identity/tenant tests. Remaining: password recovery/reset, broader audit coverage, and owner-transfer policy.

Dependencies: Phase 1. Verification so far: 4 backend tests pass.

## Phase 3 — Core inventory — IN_PROGRESS

Implemented so far: normalized organization-scoped categories, products, hubs, suppliers and supplier-product links; product/hub balances with database constraints; immutable signed stock movements; tenant-scoped DRF APIs for categories, products, hubs, suppliers, movements, dashboard summary, and product stock mutations; idempotency keys; row locking; receipt/issue/adjustment validation; negative/available-stock protection; audit records; migrations; and inventory tests.

Remaining: richer pagination/filtering, supplier workflows, reservation semantics, frontend API wiring, and additional performance/security coverage. Every quantity-changing operation must continue to use the transactional service boundary rather than direct model writes.

Dependencies: Phase 2. Verification: migration drift check, Django check, and the inventory tests are included in the current 10-test backend suite.

## Phase 4 — Restocking and transfers — IN_PROGRESS

Implemented so far: restock request state transitions `draft → pending → approved → ordered → received`, cancellation before receipt, inter-hub transfer transitions `draft → pending → approved → dispatched → received`, cancellation before dispatch, role gates, membership checks, source availability validation, row locks, idempotent restock receipt/source dispatch/destination receipt effects, immutable movement/audit records, migrations, and lifecycle tests.

Remaining: finer-grained policy per transition, supplier purchase-order integration, richer transfer metadata, cancellation/refund semantics after operational handoff, and frontend workflow screens. Verification: the full backend suite currently passes 10 tests.

Dependencies: Phases 2–3. Verification: lifecycle, insufficient-stock, idempotency, migration, and authorization checks.

## Phase 5 — Frontend application — IN_PROGRESS

The public landing page and responsive workspace shell are implemented with polished navigation, dashboard empty states, AI assistant entry, route manifest, reduced-motion support, responsive behavior, login/registration UI, typed JWT API client with refresh/logout handling, a live Overview summary query, and a permission-aware Team page wired to member/invitation/permission APIs. Inventory, Categories, Hubs, Suppliers, Restock, and Transfers now have confirmation-driven React Hook Form + Zod mutations backed by typed Django APIs, permission-aware controls, state-machine transition visibility, backend error feedback, and TanStack Query refreshes. Supplier-product relationship writes remain blocked by the current read-only backend contract.

Dependencies: Phases 2–4 for live workflows. Verification: frontend typecheck, ESLint, 7 Vitest tests, production build, and route-manifest validation pass.

Mutation milestone checkpoint: `5180c11c2a39728aa7c5f505b7d26fdb5a380edc`.

## Phase 6 — Analytics and reports — TODO

Implement deterministic risk, low-stock, stockout, valuation, slow/excess, movement, imbalance calculations, report metadata, CSV/PDF exports, storage, and optional async generation. Verify calculations against fixtures and ensure reports cannot cross tenants.

Dependencies: Phases 2–4. Verification: calculation, permissions, export, storage error, and incomplete-history tests.

## Phase 7 — AI assistant — TODO

Implement Groq adapter, persistent conversation history, bounded memory/preferences, server-side read/write tools, tool-call records, confirmation proposals, and grounded reports. Verify schemas, authorization, tenant scoping, mutation confirmation/recheck, and mocked-provider behavior.

Dependencies: Phases 2–6. Verification: tool and confirmation-flow tests; no arbitrary SQL or fabricated metrics.

## Phase 8 — Performance and reliability — TODO

Add Upstash Redis caching/rate limiting/coordination, idempotent Celery tasks, query optimization, retry/timeouts, structured logs, and outage fallbacks. Verify that caching never crosses scopes and that Redis/Celery failures do not corrupt inventory.

Dependencies: Phases 3–7. Verification: focused cache invalidation, task, rate-limit, and degraded-service tests.

## Phase 9 — QA and security — TODO

Run backend/frontend suites, formatting/linting, type checks, dependency/security checks, and critical-flow verification. Fix high-priority issues and document genuine external blockers.

Dependencies: Phases 1–8. Verification: all available checks pass or are explicitly documented with cause and scope.

## Phase 10 — Deployment readiness and handoff — TODO

Finalize Vercel, Render API/worker, Supabase, Upstash, Groq configuration, migrations, health checks, demo seed instructions, recruiter walkthrough, status, decisions, and resume handoff. Only report deployments or URLs actually confirmed by provider responses.

Dependencies: Phases 1–9. Verification: production build/start configuration, docs review, safe demo seed, and final continuity audit.
