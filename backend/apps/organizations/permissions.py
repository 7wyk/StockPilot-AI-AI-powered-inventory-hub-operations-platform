from rest_framework.permissions import BasePermission

from .models import Membership


def get_active_membership(user):
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, "profile", None)
    active_organization_id = getattr(profile, "active_organization_id", None)
    memberships = Membership.objects.filter(user=user, is_active=True).select_related("organization")
    if active_organization_id:
        membership = memberships.filter(organization_id=active_organization_id).first()
        if membership:
            return membership
    return memberships.order_by("joined_at").first()


class HasOrganizationMembership(BasePermission):
    message = "An active organization membership is required."

    def has_permission(self, request, view):
        return bool(get_active_membership(request.user))


class HasOrganizationRole(BasePermission):
    allowed_roles = frozenset()
    message = "Your organization role cannot perform this action."

    def has_permission(self, request, view):
        membership = get_active_membership(request.user)
        if not membership:
            return False
        allowed = getattr(view, "allowed_roles", self.allowed_roles)
        return membership.role in allowed


class CanManageOrganization(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN})


class CanEditInventory(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN, Membership.Role.INVENTORY_MANAGER})


class CanOperateHub(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN, Membership.Role.INVENTORY_MANAGER, Membership.Role.HUB_OPERATOR})
