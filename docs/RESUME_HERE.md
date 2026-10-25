# Resume Here — StockPilot AI

## Start here

Read `README.md`, `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `ARCHITECTURE.md`, then inspect the actual repository and `git status`. Do not assume this document is more current than source code.

## Current state

- Repository: `https://github.com/7wyk/StockPilot-AI-AI-powered-inventory-hub-operations-platform`
- Branch: `main`; Phases 1–7 are committed.
- Manus handoff checkpoint: `be28094b655833256f9d2451ff189d12dd7b2166`.
- Phase 6 analytics commit: `5396f823744bdbd7585cf908120b6130c0eb2a1f`.
- Phase 7 AI commit: see HEAD of `main`.
- Virtual environment: `.venv/` at repository root.

## What works

### Backend
- Health and OpenAPI routes
- Identity: organizations, memberships, invitations, profiles, audit events, JWT auth, tenant scoping, role-permission matrix, throttles
- Inventory: categories, products, hubs, suppliers, balances, stock movements, dashboard metrics, transactional stock operations
- Workflows: restock requests and inter-hub transfers with full state machines
- Analytics: deterministic calculations, CSV/PDF exports, storage adapter
- AI Assistant: persistent conversations, Groq LLM integration with 9 read tools + 5 write confirmation tools, all tenant-scoped, deterministic offline fallback, user preferences

### Frontend
- Premium landing page with dark-mode hero
- Responsive workspace shell with sidebar, org switcher, breadcrumbs
- Login/registration with JWT handling
- Live dashboard overview with real backend metrics
- Permission-aware Team administration
- Confirmation-driven CRUD for all domain entities (React Hook Form + Zod)
- Reports page with Recharts analytics and export controls
- AI Operations Assistant chat with conversation sidebar, tool indicators, confirmation cards, preferences drawer

### Verified test results
- 48 backend tests pass (all phases including AI)
- Frontend TypeScript check, ESLint, Vitest unit tests, and Vite production build pass

## Exact next task

Deployment readiness (Phases 8–10):
1. Verify `.env.example` has all required variables
2. Configure Render backend deployment (`render.yaml`)
3. Configure Vercel frontend deployment (`vercel.json`)
4. Set up Supabase PostgreSQL DSN
5. Configure Upstash Redis
6. Set Groq API key in production
7. Verify production CORS/allowed hosts
8. Ensure `VITE_API_URL` points to production API
9. Ensure no secrets in frontend bundle
10. Create demo seed instructions or management command

## Commands/checks

Backend (from `backend/`):
```
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe -m pytest tests/ -x -q --tb=short
```

Frontend (from `frontend/`):
```
pnpm run typecheck
pnpm run lint
pnpm run test
pnpm run build
```

## Known blockers

No Supabase, Upstash, or Groq credentials are available. Keep external adapters configurable and make missing integrations fail explicitly without breaking core tests. No deployment URL is verified. Production PostgreSQL needs a Supabase DSN; local unsupported-DSN checks use SQLite.

## Related documents

- `TODO.md` — acceptance-oriented outcomes.
- `plan.md` — implementation and design decisions.
- `docs/DECISIONS.md` — recorded trade-offs.
- `backend/README.md` — local database boundary.
