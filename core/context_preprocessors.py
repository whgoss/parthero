from core.models.users import UserOrganization


def organizations(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    memberships = UserOrganization.objects.select_related("organization").filter(
        user=user
    )
    return {
        "user_organizations": [m.organization for m in memberships],
        "current_organization": request.organization,
    }
