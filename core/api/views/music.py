from django.db import transaction
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from core.api.permissions import IsInOrganization
from core.api.serializers import PartAssetCreateSerializer, PartAssetPatchSerializer
from core.dtos.music import PartAssetsPayloadDTO, PartOptionDTO
from core.enum.music import PartAssetType
from core.services.music import (
    create_part_asset,
    delete_part_asset,
    get_part_assets,
    get_parts,
    search_for_piece,
    update_part_asset,
)


class PartAssetViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def get_serializer_class(self, data):
        if self.action == "create":
            return PartAssetCreateSerializer(data=data)
        return PartAssetPatchSerializer(data=data)

    def create(self, request, piece_id, *args, **kwargs):
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        filename = serializer.validated_data.get("filename", None)
        asset_type = serializer.validated_data.get("asset_type", None)
        part_asset = create_part_asset(
            piece_id=piece_id, filename=filename, asset_type=asset_type
        )
        response_data = part_asset.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)

    def partial_update(self, request, piece_id, part_asset_id, *args, **kwargs):
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload_status = serializer.validated_data.get("status", None)
        part_ids = serializer.validated_data.get("part_ids", None)
        part_asset = update_part_asset(
            request.organization.id, part_asset_id, part_ids, upload_status
        )
        response_data = part_asset.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)

    def list(self, request, piece_id, *args, **kwargs):
        asset_type = request.query_params.get("asset_type")
        if not asset_type or asset_type not in PartAssetType.values():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        parts = get_parts(request.organization.id, piece_id)
        part_assets = get_part_assets(
            organization_id=request.organization.id,
            piece_id=piece_id,
            asset_type=PartAssetType(asset_type),
        )

        completed_parts = set()
        for part_asset in part_assets:
            if part_asset.parts:
                for part in part_asset.parts:
                    completed_parts.add(part.id)

        missing_parts = [part for part in parts if part.id not in completed_parts]
        part_options = [
            PartOptionDTO(value=part.display_name, id=str(part.id)) for part in parts
        ]

        payload = PartAssetsPayloadDTO(
            part_assets=part_assets,
            missing_parts=missing_parts,
            part_options=part_options,
        )
        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, part_asset_id, *args, **kwargs):
        delete_part_asset(request.organization.id, part_asset_id)
        return Response(status=status.HTTP_200_OK)


class PieceSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
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

        search_text = request.query_params.get("search")
        title = request.query_params.get("title") or search_text
        composer = request.query_params.get("composer")
        sort = request.query_params.get("sort")

        results = search_for_piece(
            title=title,
            composer=composer,
            organization_id=request.organization.id,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return Response(results.model_dump(mode="json"), status=status.HTTP_200_OK)
