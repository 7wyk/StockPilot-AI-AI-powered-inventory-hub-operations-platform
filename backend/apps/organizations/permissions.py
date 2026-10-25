from rest_framework.permissions import BasePermission

from .models import Membership


class OrganizationPermission:
    MANAGE_ORGANIZATION = "organization.manage"
    MANAGE_MEMBERS = "organization.members.manage"
    MANAGE_ROLES = "organization.roles.manage"
    VIEW_INVENTORY = "inventory.view"
    CREATE_PRODUCTS = "inventory.products.create"
    EDIT_PRODUCTS = "inventory.products.edit"
    ARCHIVE_PRODUCTS = "inventory.products.archive"
    ADJUST_STOCK = "inventory.stock.adjust"
    VIEW_MOVEMENTS = "inventory.movements.view"
    MANAGE_HUBS = "hubs.manage"
    VIEW_HUB_INVENTORY = "hubs.inventory.view"
    INITIATE_TRANSFERS = "transfers.initiate"
    APPROVE_TRANSFERS = "transfers.approve"
    DISPATCH_TRANSFERS = "transfers.dispatch"
    RECEIVE_TRANSFERS = "transfers.receive"
    VIEW_SUPPLIERS = "suppliers.view"
    MANAGE_SUPPLIERS = "suppliers.manage"
    VIEW_RESTOCK = "restock.view"
    CREATE_RESTOCK = "restock.create"
    APPROVE_RESTOCK = "restock.approve"
    VIEW_REPORTS = "reports.view"
    GENERATE_REPORTS = "reports.generate"
    USE_AI = "ai.use"
    EXECUTE_AI_READ_TOOLS = "ai.tools.read"
    APPROVE_AI_WRITES = "ai.actions.approve"


ALL_ORGANIZATION_PERMISSIONS = frozenset(
    value for name, value in vars(OrganizationPermission).items() if name.isupper()
)

ROLE_PERMISSIONS = {
    Membership.Role.OWNER: ALL_ORGANIZATION_PERMISSIONS,
    Membership.Role.ADMIN: ALL_ORGANIZATION_PERMISSIONS - {OrganizationPermission.APPROVE_AI_WRITES},
    Membership.Role.INVENTORY_MANAGER: frozenset(
        {
            OrganizationPermission.VIEW_INVENTORY,
            OrganizationPermission.CREATE_PRODUCTS,
            OrganizationPermission.EDIT_PRODUCTS,
            OrganizationPermission.ARCHIVE_PRODUCTS,
            OrganizationPermission.ADJUST_STOCK,
            OrganizationPermission.VIEW_MOVEMENTS,
            OrganizationPermission.VIEW_HUB_INVENTORY,
            OrganizationPermission.VIEW_SUPPLIERS,
            OrganizationPermission.MANAGE_SUPPLIERS,
            OrganizationPermission.VIEW_RESTOCK,
            OrganizationPermission.CREATE_RESTOCK,
            OrganizationPermission.APPROVE_RESTOCK,
            OrganizationPermission.VIEW_REPORTS,
            OrganizationPermission.USE_AI,
            OrganizationPermission.EXECUTE_AI_READ_TOOLS,
        }
    ),
    Membership.Role.HUB_OPERATOR: frozenset(
        {
            OrganizationPermission.VIEW_INVENTORY,
            OrganizationPermission.VIEW_MOVEMENTS,
            OrganizationPermission.VIEW_HUB_INVENTORY,
            OrganizationPermission.INITIATE_TRANSFERS,
            OrganizationPermission.DISPATCH_TRANSFERS,
            OrganizationPermission.RECEIVE_TRANSFERS,
            OrganizationPermission.VIEW_SUPPLIERS,
            OrganizationPermission.VIEW_RESTOCK,
            OrganizationPermission.VIEW_REPORTS,
        }
    ),
    Membership.Role.ANALYST: frozenset(
        {
            OrganizationPermission.VIEW_INVENTORY,
            OrganizationPermission.VIEW_MOVEMENTS,
            OrganizationPermission.VIEW_HUB_INVENTORY,
            OrganizationPermission.VIEW_SUPPLIERS,
            OrganizationPermission.VIEW_RESTOCK,
            OrganizationPermission.VIEW_REPORTS,
            OrganizationPermission.GENERATE_REPORTS,
            OrganizationPermission.USE_AI,
            OrganizationPermission.EXECUTE_AI_READ_TOOLS,
        }
    ),
    Membership.Role.VIEWER: frozenset(
        {
            OrganizationPermission.VIEW_INVENTORY,
            OrganizationPermission.VIEW_MOVEMENTS,
            OrganizationPermission.VIEW_HUB_INVENTORY,
            OrganizationPermission.VIEW_SUPPLIERS,
            OrganizationPermission.VIEW_RESTOCK,
            OrganizationPermission.VIEW_REPORTS,
        }
    ),
}


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


def has_organization_permission(membership, permission):
    return bool(membership and permission in ROLE_PERMISSIONS.get(membership.role, frozenset()))


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


class HasOrganizationPermission(BasePermission):
    required_permission = None
    message = "Your organization role does not have permission for this action."

    def has_permission(self, request, view):
        membership = get_active_membership(request.user)
        required = getattr(self, "required_permission", None) or getattr(view, "required_permission", None)
        return has_organization_permission(membership, required) if required else bool(membership)


class CanManageOrganization(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN})


class CanEditInventory(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN, Membership.Role.INVENTORY_MANAGER})


class CanOperateHub(HasOrganizationRole):
    allowed_roles = frozenset({Membership.Role.OWNER, Membership.Role.ADMIN, Membership.Role.INVENTORY_MANAGER, Membership.Role.HUB_OPERATOR})
