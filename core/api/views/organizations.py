from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from core.api.permissions import IsInOrganization
from core.services.organizations import search_for_musician


class RosterMusicianViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, *args, **kwargs):
        try:
            limit = int(request.query_params.get("limit", 25))
        except (TypeError, ValueError):
            limit = 25
        try:
            offset = int(request.query_params.get("offset", 0))
        except (TypeError, ValueError):
            offset = 0

        limit = min(max(limit, 1), 100)
        offset = max(offset, 0)

        name = request.query_params.get("search") or request.query_params.get("name")
        instrument = request.query_params.get("instrument")
        sort = request.query_params.get("sort")

        results = search_for_musician(
            organization_id=request.organization.id,
            name=name,
            instrument=instrument,
            limit=limit,
            offset=offset,
            sort=sort,
        )

        return Response(results.model_dump(mode="json"), status=status.HTTP_200_OK)
