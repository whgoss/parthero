from core.models.users import UserOrganization
from core.dtos.organizations import OrganizationDTO


def organizations(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    memberships = UserOrganization.objects.select_related("organization").filter(
        user=user
    )
    return {
        "user_organizations": OrganizationDTO.from_models(
            [membership.organization for membership in memberships]
        ),
        "current_organization": request.organization,
    }
