# Core inventory

`InventoryBalance.on_hand` is the physical quantity currently held at a hub. `reserved` is the portion committed to an approved downstream operation and cannot exceed on-hand. `available` is computed as `on_hand - reserved` and is the quantity eligible for an issue or transfer request. Stock movements store signed `quantity_delta`, plus before/after quantities, movement type, reason, actor, and optional idempotency/reference metadata.

All balance changes must run through `apps.inventory.services.change_stock()`. It locks the balance row, validates the resulting quantity, creates the immutable movement, and records an audit event in one transaction.
