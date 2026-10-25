# Restocking and transfers

Restock requests progress through `draft → pending → approved → ordered → received`, or can be cancelled before receipt. Receipt applies one idempotent positive stock movement at the destination hub.

Transfers progress through `draft → pending → approved → dispatched → received`, or can be cancelled before dispatch. Dispatch applies one idempotent `transfer_out` movement at the source hub; receipt applies one idempotent `transfer_in` movement at the destination hub. Both transitions lock the workflow row and use the inventory transaction service.
