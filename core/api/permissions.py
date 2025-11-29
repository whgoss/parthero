from rest_framework.permissions import BasePermission
from core.models.users import UserOrganization


class IsInOrganization(BasePermission):
    """
    Organization-scoped permission:
    - User must be authenticated
    - request.organization must be set
    - User must be a member of that organization
    """

    def has_permission(self, request, view):
        user = request.user
        organization = getattr(request, "organization", None)

        if not user or not user.is_authenticated or organization is None:
            return False

        return UserOrganization.objects.filter(
            user__id=user.id, organization__id=organization.id
        ).exists()
