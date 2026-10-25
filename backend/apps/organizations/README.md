# Organizations and tenant scope

Every organization-owned query must derive membership from the authenticated user. The initial API surface is `GET /api/v1/organizations/`, which returns only active memberships, plus registration/login/refresh/logout/me under `/api/v1/auth/`.

`get_active_membership()` resolves a user's profile-selected organization when present and otherwise falls back to their earliest active membership. Future inventory viewsets should call this helper or a stricter explicit organization selector and never trust a client-supplied organization ID without rechecking membership.
