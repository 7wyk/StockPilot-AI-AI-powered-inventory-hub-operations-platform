# Inventory implementation notes

Use the active membership resolver for tenant scope. Querysets must filter by the resolved organization before returning or mutating records. Product, hub, supplier, category, and movement viewsets are already scoped this way.

Do not update `InventoryBalance` or create `StockMovement` directly from a view. Call `apps.inventory.services.change_stock()` so row locking, idempotency, available-stock checks, non-negative validation, before/after quantities, and audit logging remain atomic. Add tests for every new movement type before exposing it through the API.
