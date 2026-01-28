"""
Storefront-specific permission classes for role-based access control
"""
from rest_framework import permissions
from .models import StorefrontCustomer, StorefrontMessage


class IsStorefrontUser(permissions.BasePermission):
    """
    Allow access only to authenticated storefront customers.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return True


class IsCustomerOwner(permissions.BasePermission):
    """
    Allow access only if user is the customer or is account manager.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Check if user is the customer
        try:
            customer = StorefrontCustomer.objects.get(user=request.user)
            if hasattr(obj, 'customer') and obj.customer == customer:
                return True
        except StorefrontCustomer.DoesNotExist:
            pass

        # Check if user is account manager
        if request.user.groups.filter(name='Account Managers').exists():
            return True

        return False


class IsAccountManager(permissions.BasePermission):
    """
    Allow access only to Account Managers.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if user is in Account Managers group
        return request.user.groups.filter(name='Account Managers').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='Account Managers').exists()


class IsProductionTeam(permissions.BasePermission):
    """
    Allow access only to Production Team members.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Check if user is in Production Team group
        return request.user.groups.filter(name='Production Team').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='Production Team').exists()


class IsAccountManagerOrOwner(permissions.BasePermission):
    """
    Allow access to account managers or the customer owner.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Check if user is account manager
        if request.user.groups.filter(name='Account Managers').exists():
            return True

        # Check if user is the customer/owner
        try:
            customer = StorefrontCustomer.objects.get(user=request.user)
            if hasattr(obj, 'customer') and obj.customer == customer:
                return True
            if hasattr(obj, 'linked_customer') and obj.linked_customer == customer:
                return True
        except StorefrontCustomer.DoesNotExist:
            pass

        return False


class IsProductAdmin(permissions.BasePermission):
    """
    Allow access only to product admins/super users.
    """

    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser


class IsPublicRead(permissions.BasePermission):
    """
    Allow public read access, no auth required.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class AllowPublicCreateOnly(permissions.BasePermission):
    """
    Allow public create access (for estimates, messages), authenticated for others.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return bool(request.user and request.user.is_authenticated)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to all, write access only to owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            try:
                customer = StorefrontCustomer.objects.get(user=request.user)
                return obj.customer == customer
            except StorefrontCustomer.DoesNotExist:
                return False

        return False
