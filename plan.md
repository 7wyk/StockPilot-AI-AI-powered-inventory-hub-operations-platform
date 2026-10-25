# StockPilot AI — Implementation and Design Plan

## Scope and implementation approach

StockPilot AI is a multi-tenant inventory and hub operations SaaS. The repository will be a monorepo with a Vite/React/TypeScript frontend and a Django/DRF backend. The backend owns authentication, tenant scoping, transactional inventory mutations, auditability, deterministic analytics, reports, and Groq tool execution. PostgreSQL/Supabase is the authoritative application database; Supabase Storage is used for private files; Redis/Celery are optional runtime integrations that degrade safely when credentials are absent.

The implementation will proceed in independently verifiable phases: foundation and health checks, identity and tenancy, core inventory, transfers/restocking, frontend shell and workflows, analytics/reports, AI assistant, performance/reliability, and deployment QA. All visible controls will either call a real API path or communicate an unavailable state. Empty-database onboarding will be supported, and demo content will be created only by an explicit seed command.

The frontend will use a typed API client and TanStack Query for server state. Protected routes will render a responsive application shell with navigation, breadcrumbs, profile actions, notifications, filters, tables, drawers, confirmation dialogs, and accessible loading/error/empty states. The backend will expose `/api/v1/` endpoints and OpenAPI documentation, with server-side authorization on every organization-owned resource. Inventory balances will be changed only by transactional services that create stock movements and audit entries.

## Design direction

### Considered styles
- **Calm command center** (0.06): bright operational workspace with precise tables, rail navigation, and quiet status color.
- **Electric signal** (0.07): blue-indigo analytics surfaces with vivid attention states and restrained violet energy.
- **Editorial logistics** (0.08): highly typographic dashboards with dense but readable operational storytelling.

**Chosen style: Electric signal.**

- **Design movement:** premium B2B operations software with the clarity of modern analytics tools and the confidence of an AI command center.
- **Core principles:** show verified operational truth first; make risk legible without alarm fatigue; keep actions close to the data they change; use motion to explain state, not decorate it.
- **Color philosophy:** white and soft-neutral foundations keep dense data calm; electric blue is the product's action color; indigo marks intelligence and aggregation; violet gradients are reserved for AI moments; green, amber, and red communicate operational status with text labels as well as color.
- **Layout paradigm:** a persistent left rail anchors the workspace, while the main content uses an asymmetric KPI-to-detail flow: summary cards lead into a wide operational table and a narrower attention column rather than a uniform card grid.
- **Signature elements:** signal-line chart accents, compact “verified” data badges, and a blue-to-indigo AI insight ribbon used sparingly on decision surfaces.
- **Interaction philosophy:** every action explains what will change and what has already changed; mutations use confirmation where consequences are material; transitions are short, directional, and reversible when safe.
- **Animation:** 160–220ms enter/exit and hover transitions, staggered dashboard entrances, animated skeleton-to-content swaps, and chart reveals; all motion is disabled or simplified under `prefers-reduced-motion`.
- **Typography system:** Inter for interface density and legibility, with restrained display weights for page titles. Use a 12/14/16/20/28/36 scale and tabular numerals for metrics.
- **Brand essence:** the verified operating layer for inventory teams who need to see risk early and act with confidence; precise, capable, grounded.
- **Brand voice:** direct, calm, operational. Example lines: “Know what is moving before it becomes a stockout.” and “This recommendation is grounded in 42 verified movements.”
- **Wordmark and logo:** a compact “S” signal mark formed from three ascending inventory bars joined by a diagonal route line, paired with a wordmark that keeps `StockPilot` solid and `AI` in the signature blue.
- **Signature brand color:** Signal Blue `#2563EB`.

## Project structure

- `frontend/`: Vite React app, typed API client, route pages, reusable design system components, feature modules, and frontend tests.
- `backend/`: Django project, API configuration, apps for accounts, organizations, inventory, hubs, suppliers, movements, transfers, reports, AI, notifications, and audit; migrations and backend tests live here.
- `docs/`: deployment, security, API and resume handoff documentation.
- `.github/workflows/`: CI for backend and frontend checks.

## Dependencies and material constraints

No production credential is committed. `.env.example` documents Django, Supabase, Groq, Redis/Celery, and Vite variables. The app runs with local SQLite only for fast backend tests when an external `DATABASE_URL` is not available, while production instructions require Supabase PostgreSQL. Groq, Redis, and Supabase Storage paths remain explicitly unavailable until credentials are configured; core inventory and reporting logic must not depend on them.

## Serving and deployment

During development, Vite serves the frontend on port 3000 and proxies `/api` to Django on port 8000 when both processes are running. Render serves Django with Gunicorn and an optional Celery worker. Vercel builds `frontend/`. Supabase provides PostgreSQL and storage; Upstash provides Redis; Groq provides inference. Deployment files will keep secrets runtime-only and expose only browser-safe Vite configuration.
