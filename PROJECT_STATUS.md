# StockPilot AI — Project Status

## Current phase
Phase 1 — Foundation, complete for the current milestone; Phase 2 is next.

## Phase status
- Phase 0 — `DONE`: initialized clean scaffold inspected; continuity documents and design plan created.
- Phase 1 — `DONE` for foundation milestone: monorepo standards, environment templates, Django health/OpenAPI foundation, Vite frontend shell, route manifest, CI, tests, and deployment placeholders exist and were checked.
- Phase 2 — `TODO`: organizations, memberships, roles, profiles, migrations, and authorization.
- Phase 3 — `TODO`: core inventory, hubs, suppliers, movements, transactional balance services.
- Phase 4 — `TODO`: restock and transfer lifecycle.
- Phase 5 — `IN_PROGRESS`: public landing page and responsive application shell/empty-state routes are implemented; live domain workflows remain.
- Phase 6 — `TODO`: analytics, reports, exports, and storage.
- Phase 7 — `TODO`: Groq assistant, controlled tools, confirmation flow, history, memory.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features
- Managed Webdev project initialized at `/home/ubuntu/stockpilot`; server and database capabilities are enabled; Preview runtime is port 3000.
- Root workspace uses pnpm 11 with a checked-in `allowBuilds` policy for required `esbuild` scripts and a single root lockfile.
- Django backend foundation includes environment-driven settings, supported PostgreSQL selection with SQLite fallback for unsupported local DSNs, DRF/OpenAPI configuration, Celery configuration, and `GET /api/v1/health/`.
- React/Vite frontend foundation includes a bright responsive landing page, application shell, Overview, Inventory, Hubs, Transfers, Reports, Activity, Settings, and AI Assistant empty states, plus `frontend/public/manus-routes.json`.
- CI, environment, deployment, security, architecture, plan, TODO, decisions, and resume documents are present.

## Tests actually run
- Backend: `.venv/bin/python manage.py check` from `backend/` — passed with no issues.
- Backend: `.venv/bin/pytest -q -rs` from `backend/` — 1 passed.
- Frontend: `pnpm typecheck` — passed.
- Frontend: `pnpm lint` — passed.
- Frontend: `pnpm test` — 1 test file, 2 tests passed.
- Frontend: `pnpm build` — passed; Vite produced `frontend/dist`.
- Runtime: `curl http://127.0.0.1:3000/manus-routes.json` — HTTP response was valid JSON with the declared routes; landing HTML responded successfully.

## Git state
- Branch: `main`.
- Current milestone commit: pending immediately after this status update.
- The requested GitHub repository exists and is currently empty; active project canonical repository remains Managed by Manus until a confirmed transfer is completed.

## Known bugs and limitations
- Live domain models, authentication, organization authorization, inventory persistence, reports, AI, and external service adapters are not implemented yet.
- Host-provided `DATABASE_URL` is MySQL; the requested production target is Supabase PostgreSQL. Unsupported non-PostgreSQL DSNs intentionally fall back to SQLite for local checks and are documented in `backend/README.md`.
- `frontend/src/styles/index.css` uses Tailwind directives that are expected to be processed by PostCSS; raw CSS-language diagnostics may call them unknown outside Tailwind-aware tooling.
- No production credentials or live deployment are configured or verified.

## Exact next task
Implement Phase 2 identity and tenancy: organization, membership, role/permission models, migrations, JWT authentication endpoints, protected API foundations, and tenant-isolation tests before adding quantity-changing inventory operations.
