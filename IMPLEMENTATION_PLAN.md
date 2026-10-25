# StockPilot AI — Implementation Plan

Statuses: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

## Phase 0 — Repository inspection and planning — DONE

The managed project was initialized, the empty requested GitHub repository was inspected, and the architecture/design, acceptance TODO, status, decisions, and resume documents were created. The `Electric signal` visual direction was chosen for a bright, precise operations workspace.

## Phase 1 — Foundation — DONE

The repository contains a frontend/backend monorepo, environment examples, pnpm workspace policy and lockfile, lint/format/typecheck/test commands, Django settings and API structure, an unauthenticated health/readiness endpoint, OpenAPI documentation routes, route manifest, accessible frontend shell, CI, and initial tests. Verification completed: Django check and health test passed; frontend typecheck, lint, two Vitest tests, and Vite production build passed; the dev server served the route manifest and landing HTML.

## Phase 2 — Database and identity — IN_PROGRESS

Implemented so far: organization, membership, invitation, profile, and audit models with Django migrations; JWT registration/login/refresh/logout/me; refresh-token blacklist support; email-compatible login; tenant-scoped organization listing; active-membership resolver; and identity/tenant tests. The verified backend suite currently passes 4 tests.

Remaining acceptance work: password recovery/reset, organization switching, invitations and membership administration, explicit role permission endpoints/tests, authentication/sensitive-endpoint rate limiting, and any additional audit coverage. Verify tenant isolation and the permission matrix before high-impact inventory mutations.

Dependencies: Phase 1. Verification: auth, expiration, role, organization isolation, validation, and API permission tests.

## Phase 3 — Core inventory — TODO

Implement categories, products, hubs, suppliers, supplier relationships, balances, movements, adjustments, dashboard aggregates, secure file metadata, and transactional inventory services. Verify all consequential balance changes create immutable movements and cannot create negative balances.

Dependencies: Phase 2. Verification: CRUD, query scope/pagination, transaction integrity, movement consistency, and empty-database onboarding.

## Phase 4 — Transfers and restocking — TODO

Implement transparent restock suggestions, transfer state transitions, approval roles, idempotency/concurrency protections, and audit/movement records. Verify duplicate dispatch/receipt protection, source availability, and permission enforcement.

Dependencies: Phase 3. Verification: lifecycle, concurrency, rollback, and authorization tests.

## Phase 5 — Frontend application — IN_PROGRESS

The public landing page and responsive workspace shell are implemented with polished navigation, dashboard empty states, AI assistant entry, route manifest, reduced-motion support, and responsive behavior. Live domain workflows remain to be connected after Phases 2–4.

Dependencies: Phase 1 for shell, Phases 2–4 for live workflows. Verification: frontend component/page/action tests and a responsive route audit.

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
