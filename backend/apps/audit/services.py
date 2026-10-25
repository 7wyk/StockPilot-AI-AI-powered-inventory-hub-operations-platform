from .models import AuditLog


def record_audit(*, organization, actor, action, outcome="success", resource_type="", resource_id="", metadata=None, request_id=""):
    return AuditLog.objects.create(
        organization=organization,
        actor=actor,
        action=action,
        outcome=outcome,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        metadata=metadata or {},
        request_id=request_id,
    )
