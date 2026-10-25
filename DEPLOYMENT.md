# Deployment Guide

## Target topology

Build `frontend/` as a Vercel static SPA. Run the Django API from `backend/` on Render with Gunicorn. If report generation or other genuinely slow tasks require it, run a separately configured Render worker using the same backend image and Celery command. Use Supabase PostgreSQL as the authoritative database and Supabase Storage for private objects, Upstash Redis for disposable cache/rate-limit/Celery coordination, and Groq for server-side AI inference.

## Required configuration

Start from `.env.example`. Put Django secret, database DSN, Supabase service-role key, Groq key, Redis/Celery URLs, and JWT configuration in Render's protected environment. Put only `VITE_API_URL` and other explicitly public values in Vercel. Never place database, Groq, Django, or Supabase service-role credentials in frontend code.

## Build and start commands

Frontend: from `frontend/`, run `pnpm install --frozen-lockfile` and `pnpm build`; publish `frontend/dist`. Backend: install `backend/requirements.txt`, run `python manage.py migrate`, collect static assets if configured, and start `gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:$PORT`. Worker, when enabled: `celery -A config worker --loglevel=INFO` from `backend/`. Configure Render health checks to `/api/v1/health/`.

## Database and storage

Create Supabase database/storage resources and apply Django migrations from the release environment. Configure a private storage bucket and server-side signed URL/upload flows. Development and production should use separate Supabase projects where possible; do not treat a local SQLite database as a production substitute.

## Operational caveats

Render sleeping/free-tier behavior, provider quotas, Redis protocol compatibility, Groq rate limits, and Supabase storage policies vary by plan and can change. The application must surface provider outages as explicit configuration/service errors. No deployment URL is considered verified until the provider reports a successful deployment and the health/build checks pass.
