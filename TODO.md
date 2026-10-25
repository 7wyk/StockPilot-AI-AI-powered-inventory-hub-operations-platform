# StockPilot AI — Delivery TODO

Status values: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`. An item is `DONE` only when the behavior exists and relevant checks have evidence.

## Foundation and continuity — IN_PROGRESS
- [ ] The repository contains a maintainable frontend/backend monorepo, environment examples, lockfiles, coding standards, CI, and durable continuity files.
- [ ] The project exposes a versioned `/api/v1/` API, an unauthenticated health/readiness check, structured errors, OpenAPI documentation, and documented local/production commands.
- [ ] Frontend routes are represented in `frontend/public/manus-routes.json` and remain synchronized with the route source.

## Identity, tenancy, roles — TODO
- [ ] Registration, login, logout, password recovery, access/refresh handling, protected routes, expired-session handling, and user profiles work through the documented authentication design.
- [ ] Organization-owned resources are always scoped from the authenticated server-side identity; client-supplied organization IDs are never the sole authorization boundary.
- [ ] Owner, Administrator, Inventory Manager, Hub Operator, Analyst, and Read-only Viewer permissions are enforced on the backend for inventory reads, stock changes, transfer approvals, reports, team administration, and AI tools.
- [ ] Important administrative and inventory actions create audit records, and authentication/sensitive endpoints have sensible rate limits.

## Core inventory — TODO
- [ ] Products support name, SKU, description, category, unit, image, cost, optional selling price, reorder threshold, target level, active/archive status, and timestamps, with search, sorting, filtering, pagination, CRUD, and secure image upload flows.
- [ ] Categories, hubs, suppliers, supplier-product relationships, hub-specific balances, and empty-database onboarding are implemented with organization scoping and indexes/constraints.
- [ ] Available, reserved, and on-hand quantity semantics are defined in documentation and used consistently.
- [ ] Receipts, issues, adjustments with reasons, and stock movement history use PostgreSQL transactions; every consequential quantity change creates an auditable movement and cannot make stock negative.
- [ ] Dashboard KPIs are derived from authenticated organization records, including products, units, valuation, low/out-of-stock items, hub distribution, movement trends, slow-moving indicators, transfers, activity, and useful filters.

## Transfers and restocking — TODO
- [ ] Restock calculations identify below-threshold products and calculate transparent target-minus-eligible-stock suggestions; users can review/edit quantities before saving a request.
- [ ] Restock requests distinguish internal drafts from external supplier orders and never claim an external purchase was placed without a real integration.
- [ ] Hub transfers validate source/destination and available source quantity, use explicit pending/approved/dispatched/received/cancelled states, and preserve movement history at both locations.
- [ ] Transfer approval, dispatch, and receipt are permission-protected, transactional, concurrency-safe, idempotent, and protected from duplicate operations and negative quantities.

## Frontend product experience — TODO
- [ ] The public landing page, onboarding, authentication screens, responsive shell, breadcrumbs, profile menu, notifications, global search, and contextual actions are polished and usable on mobile through desktop.
- [ ] Required product, category, hub, supplier, movement, transfer, risk, report, AI, notification, team, profile, audit, and settings pages exist; every visible control works or is clearly unavailable.
- [ ] Loading/skeleton, empty, validation, permission, network error, toast, confirmation, reduced-motion, keyboard navigation, and accessible focus states are implemented.

## Analytics, reports, storage — TODO
- [ ] Deterministic calculations exist for low stock, stockouts, reorder suggestions, valuation, slow-moving and excess candidates, movement summaries, hub imbalance, and basic risk ranking; unsupported sales/demand metrics are not fabricated.
- [ ] Inventory health, low-stock/stockout, valuation, slow-moving, hub performance, movement, transfer, and monthly operational reports use validated database results, include scope/period/timestamp/limitations, and provide CSV/PDF download flows.
- [ ] Product images, private reports, avatars, supplier documents, and optional import files use server-side validation and private storage/signed access where applicable.

## AI assistant — TODO
- [ ] Persistent conversations/messages, rename/list/delete/continue, tool-call metadata/results, bounded memory/preferences, and context summarization are stored per user and organization without sensitive secrets.
- [ ] Server-side AI tools have explicit schemas, authorization, tenant scoping, query limits, error handling, and read/write classification; the model never runs arbitrary SQL or sees credentials.
- [ ] AI answers are grounded in actual tool results, recommendations are separated from verified measurements, and state-changing actions show exact products/quantities/hubs and require user confirmation before a transactional recheck/commit.
- [ ] AI-generated reports are based on validated application calculations and clearly qualify incomplete historical data.

## Reliability, QA, deployment — TODO
- [ ] Upstash Redis is used only for appropriately scoped caching/rate limiting/coordination, with graceful outage behavior and invalidation after mutations; authoritative balances remain in PostgreSQL.
- [ ] Suitable long-running reports use idempotent Celery tasks with retry/timeout policy and observable task identifiers.
- [ ] Backend pytest/pytest-django and frontend Vitest/RTL tests cover auth/permissions, tenant isolation, inventory integrity, transfers/restock, reports, AI tool authorization/confirmation, validation, critical screens/forms/filters/actions/downloads, and failure states.
- [ ] CI runs dependency installation, formatting/linting, TypeScript checks, and available tests without marking failures successful.
- [ ] Vercel, Render API/worker, Supabase, Upstash, and Groq configuration, migrations, health checks, secrets, CORS, troubleshooting, demo seeding, and recruiter walkthrough are documented without fabricated deployment claims.
