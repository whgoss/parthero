from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from core.api.permissions import IsInOrganization
from core.services.domo import search_for_piece as search_for_domo_piece


class DomoWorkSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, *args, **kwargs):
        title = request.query_params.get("title")
        composer = request.query_params.get("composer")

        domo_results = []
        if title or composer:
            domo_results = search_for_domo_piece(title=title, composer=composer)

        response_data = [work.model_dump(mode="json") for work in domo_results]
        return Response(response_data, status=status.HTTP_200_OK)
