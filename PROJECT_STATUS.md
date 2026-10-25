# StockPilot AI — Project Status

## Current phase
Phase 7 — AI Operations Assistant, complete. Phases 6 and 7 are implemented, tested, and committed. Development continues toward deployment readiness.

## Phase status
- Phase 0 — `DONE`: repository inspection, design, continuity documents.
- Phase 1 — `DONE`: monorepo foundation, Django health/OpenAPI, responsive Vite shell, CI, and first checks.
- Phase 2 — `DONE`: organization, membership, role, profile, audit models and migrations; JWT registration/login/refresh/logout/me; tenant-scoped organization listing; active organization switching; invitation/member administration; server-authoritative role matrix; configurable throttles; action-level enforcement. Password recovery and owner transfer remain out of scope for MVP.
- Phase 3 — `DONE`: categories, products, hubs, suppliers, balances, immutable stock movements, tenant-scoped APIs, dashboard summary, idempotent transactional receipt/issue/adjustment service, and inventory tests.
- Phase 4 — `DONE`: restock request and inter-hub transfer state machines with permission gates, membership checks, availability validation, idempotent stock effects, movement/audit records, migrations, and lifecycle tests.
- Phase 5 — `DONE`: public landing page, responsive shell, login/registration, typed auth client, refresh/logout handling, route manifest, live dashboard summary, permission-aware Team page, confirmation-driven mutation workflows for all domain entities.
- Phase 6 — `DONE`: deterministic analytics (inventory value, total units, products, hubs, low-stock/out-of-stock counts, inventory by hub, movement trends, low-stock table), CSV/PDF exports, storage adapter, frontend Reports page with Recharts.
- Phase 7 — `DONE`: Groq adapter with offline fallback, persistent conversations/messages, bounded memory/preferences, 9 read tools + 5 write confirmation tools, tool-call records, confirmation proposals with server-side validation, tenant-scoped authorization, polished React chat UI at `/app/assistant`.
- Phase 8 — `TODO`: Redis/Celery, caching, rate limits, performance and reliability.
- Phase 9 — `TODO`: full QA/security pass.
- Phase 10 — `TODO`: deployment readiness and handoff.

## Completed features

### Backend
The backend includes organization, membership, invitation, profile, and audit models; JWT access/refresh with blacklist support; transactional registration; email-compatible login; tenant-scoped organization listing; active-membership resolver; member and invitation administration; secure invitation acceptance; membership audit events; role-permission matrix; configurable throttles; action-level permission enforcement.

Core inventory: organization-scoped categories, products, hubs, suppliers, supplier-product links, product/hub balances, immutable signed stock movements, tenant-scoped APIs, dashboard metrics, idempotency keys, row locking, negative-stock protection, available-stock validation, audit events.

Operational workflows: restock requests (draft → pending → approved → ordered → received, with cancellation), inter-hub transfers (draft → pending → approved → dispatched → received, with cancellation), idempotent stock effects, movement/audit records.

Analytics: deterministic risk, low-stock, stockout, valuation, movement calculations; report metadata; CSV/PDF exports; configurable storage adapter.

AI assistant: persistent conversations and messages; Groq LLM integration with tool-calling; 9 read tools (inventory_summary, low_stock_products, out_of_stock_products, hub_inventory, product_search, recent_movements, restock_requests, transfer_requests, supplier_list); 5 write confirmation tools (receive_stock, issue_stock, adjust_stock, create_transfer, create_restock_request); all tools tenant-scoped via active membership; write tools return structured confirmation proposals; confirmed actions delegate to existing transactional services; deterministic rule-based offline fallback; user preferences/memory.

### Frontend
Public landing page with premium design. Responsive workspace shell with organization switcher, breadcrumbs, sidebar navigation. Login/registration forms. Live dashboard with real backend metrics. Permission-aware Team page. Confirmation-driven mutation dialogs for inventory, categories, hubs, suppliers, restock, and transfers using React Hook Form + Zod. Reports page with Recharts analytics and CSV/PDF export controls. AI Operations Assistant chat UI with persistent conversation list, message history, tool execution indicators, interactive confirmation cards, and user preferences drawer.

## Tests actually run

- Foundation backend: Django check and health test passed.
- Foundation frontend: typecheck, lint, 2 Vitest tests, production build.
- Phase 2–4 backend: migration drift checks, Django check, 18 backend tests (role enforcement, throttling, tenant isolation).
- Phase 5 frontend: typecheck, ESLint, 7 Vitest tests, production build.
- Phase 6: analytics calculation tests, export tests, permission tests, tenant isolation tests.
- Phase 7: 48 backend tests (conversation tenant isolation, user permissions, read tool correctness, write confirmation requirement, confirmed transaction execution, audit logging, cross-tenant ID rejection, invalid argument rejections, scoped user preferences). Frontend: AssistantPage rendering, message submission, conversation loading, confirmation cards, confirm/cancel actions.
- Final build: TypeScript compilation + Vite production build passed.

## Git state

- Branch: `main`.
- Manus handoff checkpoint: `be28094b655833256f9d2451ff189d12dd7b2166`.
- Phase 6 analytics commit: `5396f823744bdbd7585cf908120b6130c0eb2a1f`.
- Phase 7 AI commit: pending (working tree changes staged).

## Known bugs and limitations

Password recovery, broader audit coverage, owner transfer, supplier-product relationship write APIs, and external service adapters are not complete. Throttles use Django's disposable cache and should move to tenant-safe Upstash coordination. The host-provided `DATABASE_URL` may be MySQL; unsupported non-PostgreSQL DSNs fall back to SQLite for local checks, while production targets Supabase PostgreSQL. No production credentials or live deployment are configured.

## Exact next task

Phase 8–10: deployment readiness — verify/fix `.env.example`, Render config, Vercel config, Supabase PostgreSQL, Upstash Redis, Groq config, production CORS/hosts, `VITE_API_URL`, ensure no secrets in frontend.
