from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from core.api.permissions import IsInOrganization
from core.services.organizations import search_for_musician


class MusicianSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, *args, **kwargs):
        name = request.query_params.get("name")
        instrument = request.query_params.get("instrument")

        results = []
        if name or instrument:
            results = search_for_musician(
                organization_id=request.organization.id,
                name=name,
                instrument=instrument,
            )

        response_data = [result.model_dump(mode="json") for result in results]
        return Response(response_data, status=status.HTTP_200_OK)
