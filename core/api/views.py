from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from core.api.serializers import (
    PartAssetCreateSerializer,
    PartAssetPatchSerializer,
)
from core.services.music import (
    create_part_asset,
    update_part_asset,
)
from core.api.permissions import IsInOrganization


class PartAssetViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def get_serializer_class(self, data):
        if self.action == "create":
            return PartAssetCreateSerializer(data=data)
        return PartAssetPatchSerializer(data=data)

    @transaction.atomic
    def create(self, request, piece_id, *args, **kwargs):
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        filename = serializer.validated_data.get("filename", None)
        part_asset = create_part_asset(piece_id, filename)
        response_data = part_asset.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, piece_id, part_asset_id, *args, **kwargs):
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload_status = serializer.validated_data.get("status", None)
        part_ids = serializer.validated_data.get("part_ids", None)
        part_asset = update_part_asset(part_asset_id, part_ids, upload_status)
        response_data = part_asset.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)
