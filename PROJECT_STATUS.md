# StockPilot AI — Project Status

## Current phase
Phase 2 — Database and identity, in progress.

## Phase status
- Phase 0 — `DONE`: repository inspection, design, continuity documents.
- Phase 1 — `DONE`: monorepo foundation, Django health/OpenAPI, responsive Vite shell, CI, and first checks.
- Phase 2 — `IN_PROGRESS`: organization, membership, role, profile, audit models and migrations; JWT registration/login/refresh/logout/me; tenant-scoped organization listing; identity/tenant tests are implemented. Password recovery, invitation/team administration, organization switching, and full role matrix enforcement remain.
- Phase 3 — `TODO`: core inventory, hubs, suppliers, movements, transactional balance services.
- Phase 4 — `TODO`: restock and transfer lifecycle.
- Phase 5 — `IN_PROGRESS`: public landing page and responsive shell/empty states are implemented; live workflows remain.
- Phase 6 — `TODO`: analytics, reports, exports, and storage.
- Phase 7 — `TODO`: Groq assistant, controlled tools, confirmation flow, history, memory.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features

The managed Webdev project is at `/home/ubuntu/stockpilot` with server/database capabilities enabled and Preview runtime port 3000. The root pnpm workspace has a reviewed `allowBuilds` policy for esbuild and one lockfile.

The backend includes organization, membership, invitation, profile, and audit models; Django migrations; SimpleJWT access/refresh configuration with blacklist support; registration that transactionally creates a user, organization, owner membership, profile, and audit event; email-compatible login; refresh, logout, and current-user endpoints; and a tenant-scoped active organization list. Backend helpers resolve active membership from server-side profile/membership records; they do not trust client organization IDs.

The frontend landing page and responsive shell remain available with honest empty states for the domain screens. CI, environment, deployment, security, architecture, plan, TODO, decisions, and resume documents are present.

## Tests actually run

- Foundation backend: Django check passed; health test passed.
- Foundation frontend: typecheck, lint, 2 Vitest tests, and production build passed; `/manus-routes.json` and landing HTML responded from Vite.
- Phase 2 backend: `cd backend && ../.venv/bin/pytest -q -rs` — 4 passed; Django check passed after migrations.

## Git state

- Branch: `main`.
- Phase 1 foundation commit: `a71c7025b2f04232520b11f2912a23b473210d86`.
- Phase 2 identity milestone commit: `f666781bfd428c7e05c38a691905f7954c96094d`.
- Phase 2 identity milestone commit: `f666781bfd428c7e05c38a691905f7954c96094d`.
- The requested GitHub repository is empty; the canonical-transfer confirmation was declined. The managed repository remains canonical, and no plain GitHub push was attempted.

## Known bugs and limitations

Live inventory domain models, password recovery, invitation/team administration, organization switching, full role enforcement, reports, AI, and external service adapters are not complete. The host-provided `DATABASE_URL` is MySQL; unsupported non-PostgreSQL DSNs intentionally fall back to SQLite for local checks, while production documentation targets Supabase PostgreSQL. No production credentials or live deployment are configured or verified.

## Exact next task

Complete Phase 2 with password recovery/reset flow, organization switching, invitations and membership management, explicit role permission tests/endpoints, and rate limiting on authentication/sensitive endpoints. Then begin Phase 3 category/product/hub/supplier models before any quantity-changing operations.
