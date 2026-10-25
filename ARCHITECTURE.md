# StockPilot AI — Architecture

## System shape

StockPilot AI is a browser frontend backed by a versioned Django REST API. The frontend owns presentation, route protection, form validation, query caching, and mutation confirmation UI. Django is the only authority for identity, tenant scope, permissions, inventory state, auditability, report calculations, file authorization, and AI tool execution.

Production target: Vercel serves `frontend/`; Render serves Django/Gunicorn and an optional Celery worker; Supabase provides PostgreSQL and private object storage; Upstash provides Redis; Groq provides inference. Local development may use SQLite for deterministic backend tests when `DATABASE_URL` is absent, but production is documented around Supabase PostgreSQL.

## Data flow

1. Browser calls relative `/api/v1/` endpoints through a typed client.
2. Django authenticates the request and resolves the user and active organization from server-side identity/membership state.
3. Query services filter by organization and apply permissions, limits, pagination, and optimized relations.
4. Mutations enter transactional domain services, lock affected balances where needed, update authoritative rows, append stock movements/audit records, invalidate scoped caches, and return the saved result.
5. Reports reuse deterministic calculation services; heavy generation may enqueue an idempotent Celery task and store metadata/file bytes through the server-side storage adapter.
6. AI requests build bounded, permission-aware context and call Groq with explicit tool schemas. Tool execution happens in Django only; write tools return proposals until the user confirms, then revalidate and commit transactionally.

## Backend modules

- `config/`: settings, URLs, WSGI/ASGI, API versioning, OpenAPI, health/readiness, Celery, logging, CORS, JWT configuration.
- `apps/accounts/`: user/profile/session/token flows.
- `apps/organizations/`: organizations, memberships, roles, permission matrix, tenant scope.
- `apps/inventory/`: products, categories, inventory balances, transactional stock services.
- `apps/hubs/`: hub CRUD and hub-level inventory views.
- `apps/suppliers/`: suppliers and product relationships.
- `apps/movements/`: immutable stock movement records, reasons, adjustments.
- `apps/transfers/`: transfer state machine, idempotency, concurrency, movement creation.
- `apps/reports/`: deterministic analytics, report metadata/export generation.
- `apps/ai/`: conversations, messages, memory/preferences, Groq adapter, schemas, permission-aware tools.
- `apps/notifications/`: in-app notification records and read state.
- `apps/audit/`: append-only consequential action records.

## Database conventions

Every organization-owned table has an organization foreign key or an unambiguous organization-owned parent, indexes the tenant plus common filter columns, and is queried through tenant-scoped services/viewsets. Uniqueness constraints include organization scope. Money uses decimal fields with documented currency assumptions; quantities are non-negative decimals/integers as appropriate. Inventory balances are authoritative; stock movements are immutable facts and adjustments reference reasons. Django migrations are the sole schema source of truth.

Core relationships: Organization -> Membership/User; Organization -> Category/Product/Hub/Supplier; Product + Hub -> InventoryBalance; Product/Hub -> StockMovement; Supplier + Product -> SupplierProduct; RestockRequest -> RestockItem -> Product/Hub; Transfer -> TransferItem -> Product and source/destination Hubs; Organization/User -> AuditLog/Notification/Conversation/Report.

## API conventions

Endpoints use `/api/v1/`, nouns for resources, explicit action endpoints for state transitions, standard HTTP status codes, paginated list envelopes, structured validation errors, and OpenAPI schemas. No client-supplied organization identifier is trusted as an authorization boundary. Health is unauthenticated and never exposes secrets.

## Authentication and authorization

The product brief requests Django REST Framework SimpleJWT. Access/refresh handling, logout invalidation strategy, password recovery, CORS, and rate limiting are configured server-side. Authorization is represented by organization membership roles and explicit backend permission classes. The frontend only hides or disables controls for UX; backend checks are mandatory. Long-lived credentials are not stored in unsafe browser storage. If the managed Webdev Preview auth is used for preview-only access, the platform cookie contract is preserved and is not treated as the application's production organization identity.

## AI tool execution

Read-only tools return calculated organization-scoped results with bounded inputs. Write tools create a proposal and confirmation payload; the confirmed request is re-authorized, revalidated against current balances/permissions, and committed in an idempotent transaction. The model never receives credentials, arbitrary SQL access, or unbounded transcript/memory. Tool calls, results, rejected attempts, and successful consequential actions are recorded with safe metadata.

## Cache and background jobs

Redis keys always include organization and relevant user scope, have TTLs, and are disposable. PostgreSQL remains authoritative. Cache failures fall back to direct reads. Celery is reserved for long-running report/file work and similar asynchronous tasks, with idempotency keys, retry limits, timeouts, and task identifiers. Normal CRUD and quick analytics remain synchronous.

## External service boundaries

Supabase adapter: PostgreSQL DSN plus server-only Storage client; no service-role key reaches the browser. Groq adapter: server-only API key and model setting; disabled path returns an explicit configuration error. Upstash adapter: optional Redis URL/token; cache/rate-limit integration is disposable. Vercel/Render deployment files and docs never embed secrets.
