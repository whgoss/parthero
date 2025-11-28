from django.utils.deprecation import MiddlewareMixin
from core.models.users import UserOrganization


class OrganizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.organization = None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        organization_id = request.session.get("organization_id")

        try:
            if organization_id:
                membership = UserOrganization.objects.select_related(
                    "organization"
                ).get(user=user, organization_id=organization_id)
            else:
                membership = (
                    UserOrganization.objects.select_related("organization")
                    .filter(user=user)
                    .first()
                )
            if not membership:
                return
            else:
                request.session["organization_id"] = str(membership.organization.id)
        except UserOrganization.DoesNotExist:
            request.session.pop("organization_id", None)
            return

        request.organization = membership.organization
