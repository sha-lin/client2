from rest_framework import permissions


def _in_group(user, group_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=group_name).exists()


class IsAdmin(permissions.BasePermission):
    """Allow Admin group members or superusers."""

    def has_permission(self, request, view):
        return _in_group(request.user, "Admin")


class IsAccountManager(permissions.BasePermission):
    """Allow Account Manager group members or superusers."""

    def has_permission(self, request, view):
        return _in_group(request.user, "Account Manager")


class IsProductionTeam(permissions.BasePermission):
    """Allow Production Team group members or superusers."""

    def has_permission(self, request, view):
        return _in_group(request.user, "Production Team")


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: Admins/Superusers always allowed; otherwise user must own the object.
    """

    def has_object_permission(self, request, view, obj):
        if _in_group(request.user, "Admin"):
            return True
        owner = getattr(obj, "created_by", None) or getattr(obj, "owner", None)
        return owner == request.user

