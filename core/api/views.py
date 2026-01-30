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
    delete_part_asset,
    search_for_piece,
    get_part_assets,
    get_parts,
)
from core.services.domo import search_for_piece as search_for_domo_piece
from core.services.programs import add_piece_to_program, remove_piece_from_program
from core.models.programs import Program
from core.api.permissions import IsInOrganization
from core.dtos.music import PartAssetsPayloadDTO, PartAssetDTO


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

    def list(self, request, piece_id, *args, **kwargs):
        parts = get_parts(piece_id)
        part_assets = get_part_assets(piece_id)

        # Find all parts that have an asset assigned
        completed_parts = set()
        for part_asset in part_assets:
            if part_asset.parts:
                for part in part_asset.parts:
                    completed_parts.add(part.id)

        # Find all parts that don't have an asset assigned
        missing_parts = [part for part in parts if part.id not in completed_parts]

        # Find all unassigned parts
        part_options = parts

        part_assets_response = [
            part_asset.model_copy(update={"parts": part_asset.parts or []})
            if isinstance(part_asset, PartAssetDTO)
            else part_asset
            for part_asset in part_assets
        ]

        payload = PartAssetsPayloadDTO(
            part_assets=part_assets_response,
            missing_parts=missing_parts,
            part_options=part_options,
        )
        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, part_asset_id, *args, **kwargs):
        delete_part_asset(part_asset_id)
        return Response(status=status.HTTP_200_OK)


class PieceSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, *args, **kwargs):
        title = request.query_params.get("title")
        composer = request.query_params.get("composer")

        results = []
        if title or composer:
            results = search_for_piece(
                title=title,
                composer=composer,
                organization_id=request.organization.id,
            )

        response_data = [result.model_dump(mode="json") for result in results]
        return Response(response_data, status=status.HTTP_200_OK)


class ProgramPieceViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    @transaction.atomic
    def update(self, request, program_id, piece_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        pieces = add_piece_to_program(program_id, piece_id)
        response_data = [piece.model_dump(mode="json") for piece in pieces]
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, program_id, piece_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        pieces = remove_piece_from_program(program_id, piece_id)
        response_data = [piece.model_dump(mode="json") for piece in pieces]
        return Response(response_data, status=status.HTTP_200_OK)


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
