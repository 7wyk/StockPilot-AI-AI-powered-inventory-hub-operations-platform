# StockPilot API

The production target is Supabase PostgreSQL. The Manus managed development environment exposes a MySQL `DATABASE_URL`; this backend intentionally ignores unsupported non-PostgreSQL DSNs and uses local SQLite for deterministic checks instead. Configure a `postgres://` or `postgresql://` `DATABASE_URL` to exercise the production database adapter.

Run locally from the repository root with `.venv/bin/python backend/manage.py check`. Run backend tests from `backend/` with `../.venv/bin/pytest -q`.
