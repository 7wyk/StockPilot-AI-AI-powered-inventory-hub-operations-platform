# Security Notes

StockPilot AI is multi-tenant. Every organization-owned resource is scoped from the authenticated server-side user and membership, never from a client-provided organization ID alone. Backend permission checks are mandatory even when the frontend hides a control.

Inventory mutations are transactional, validate quantities and state transitions, and append an immutable movement plus audit record. Transfer dispatch/receipt and AI write tools recheck permissions and current balances immediately before committing. Idempotency keys and unique constraints prevent duplicate consequential operations.

Secrets stay server-side. The browser must never receive `DJANGO_SECRET_KEY`, database credentials, Supabase service-role keys, Groq keys, or Redis tokens. Uploaded files are untrusted: validate size/type/name, store through a server-side adapter, and use private storage/signed access for protected content. User-provided text and database content are untrusted model input and must not become executable instructions or SQL.

Use secure HTTPS deployment, restrictive CORS/CSRF configuration, short-lived access tokens with an explicit refresh/revocation strategy, rate limits on authentication/sensitive endpoints, structured logs without secrets, dependency updates, and audit records for administrative/inventory/AI actions. If embedded Preview cookies are used, preserve the platform contract and use `SameSite=None; Secure` for HTTPS cross-site iframe requests rather than deriving those flags from the internal HTTP connection.

Known external verification still required: production CORS/CSRF origins, provider storage policies, Supabase/PostgreSQL locking behavior, Redis rate-limit behavior, and deployment secret scanning.
