# StockPilot AI — Decision Log

## 2026-10-25 — Use an explicit monorepo

**Decision:** Keep `frontend/` and `backend/` clearly separated under one repository, with root documentation and CI. **Reason:** the brief requires React/Vite and Django/DRF as distinct deployable units while preserving one durable handoff surface.

## 2026-10-25 — Django remains the production API authority

**Decision:** Do not replace the requested Django/SimpleJWT/DRF stack with the managed Webdev starter's default framework/auth. **Reason:** the brief explicitly requires Django, SimpleJWT, tenant-aware authorization, and server-side inventory transactions. The managed platform's server/database capability is infrastructure context, not permission to silently change the product architecture.

## 2026-10-25 — PostgreSQL/Supabase is the documented production database

**Decision:** Production environment variables and deployment docs target Supabase PostgreSQL and Supabase Storage. Local tests may use SQLite only as a deterministic convenience when PostgreSQL credentials are unavailable. **Trade-off:** SQLite cannot prove PostgreSQL-specific locking/index behavior; integration checks must be run when Supabase credentials are configured.

## 2026-10-25 — Database is authoritative for inventory

**Decision:** Redis is disposable for caching, rate limiting, and coordination only. Stock balances and immutable movement facts live in PostgreSQL. **Reason:** avoiding stale or cross-tenant inventory and preserving correctness during Redis outages.

## 2026-10-25 — AI is a controlled server tool caller

**Decision:** Groq receives bounded context and explicit schemas; Django validates and authorizes every tool call. Write operations are proposals until UI confirmation, followed by a fresh transactional validation. **Reason:** the brief forbids arbitrary SQL, fabricated metrics, credential exposure, and unconfirmed mutations.

## 2026-10-25 — Canonical repository starts Managed by Manus

**Decision:** Use the initialized managed repository for checkpoints until the platform's GitHub canonical-transfer confirmation is completed. **Reason:** the requested GitHub repo is empty, and the platform requires its own owner-confirmed transfer flow; a plain `gh` push would not switch the managed project's canonical source.

## 2026-10-25 — Bright “Electric signal” visual language

**Decision:** Use white/neutral surfaces, Signal Blue `#2563EB`, indigo intelligence accents, restrained violet gradients, and semantic status colors. **Reason:** it matches the requested bright modern SaaS direction while keeping dense operational data legible and calm.
