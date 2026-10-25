# StockPilot AI

StockPilot AI is an AI-enhanced inventory and hub operations platform for teams that need verified stock visibility, risk detection, restocking and transfers, operational reporting, and a permission-aware assistant in one workspace.

## Repository status

This repository is being built incrementally from the product brief in `pasted_content.txt` supplied to the initial session. Read [`PROJECT_STATUS.md`](PROJECT_STATUS.md), [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/RESUME_HERE.md`](docs/RESUME_HERE.md) before continuing work in a new session.

## Planned stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui patterns, Framer Motion, Lucide, Recharts, TanStack Query, React Router, React Hook Form, Zod.
- Backend: Python, Django, Django REST Framework, SimpleJWT, drf-spectacular, Gunicorn, pytest/pytest-django.
- Production services: Supabase PostgreSQL/Storage, Upstash Redis, Celery, Groq, Vercel, Render, GitHub Actions.

## Development principles

The database is authoritative. Every consequential stock quantity change is transactional, validated, and auditable. Every organization-owned request is tenant-scoped from authenticated server identity. AI recommendations are distinct from verified measurements; mutations require explicit confirmation and a second server-side validation. No credentials or fabricated live metrics belong in source code.

## Current implementation

Phase 0 planning is in progress. The project directory is initialized and the foundation is the next implementation milestone. Features are not complete until the status and handoff documents contain evidence from actual checks.

## Local commands

Commands will be added as the frontend and backend manifests land. Production deployment guidance will live in [`DEPLOYMENT.md`](DEPLOYMENT.md); security assumptions and threat controls will live in [`SECURITY.md`](SECURITY.md).

## Demo data

Demo data will be created only through an explicit, documented seed command. It will never be inserted automatically on startup and will never include production credentials.
