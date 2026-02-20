from django.db import transaction
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from core.api.permissions import IsInOrganization
from core.api.serializers import (
    ProgramChecklistPatchSerializer,
    ProgramMusicianCreateSerializer,
    ProgramMusicianInstrumentSerializer,
)
from core.models.programs import Program
from core.services.programs import (
    add_musician_to_program,
    add_musicians_to_program,
    add_piece_to_program,
    add_program_musician_instrument,
    get_pieces_for_program,
    get_program_checklist,
    get_musicians_for_program,
    search_for_programs,
    remove_musician_from_program,
    remove_piece_from_program,
    remove_program_musician_instrument,
    update_program_checklist,
)


class ProgramPieceViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        pieces = get_pieces_for_program(request.organization.id, program_id)
        response_data = [piece.model_dump(mode="json") for piece in pieces]
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def update(self, request, program_id, piece_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        pieces = add_piece_to_program(request.organization.id, program_id, piece_id)
        response_data = [piece.model_dump(mode="json") for piece in pieces]
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, program_id, piece_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        pieces = remove_piece_from_program(
            request.organization.id, program_id, piece_id
        )
        response_data = [piece.model_dump(mode="json") for piece in pieces]
        return Response(response_data, status=status.HTTP_200_OK)


class ProgramSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
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

        name = request.query_params.get("search") or request.query_params.get("name")
        sort = request.query_params.get("sort")
        results = search_for_programs(
            organization_id=request.organization.id,
            name=name,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return Response(results.model_dump(mode="json"), status=status.HTTP_200_OK)


class ProgramMusicianViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    @transaction.atomic
    def create(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        serializer = ProgramMusicianCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        musician_id = serializer.validated_data.get("musician_id", None)
        principals = serializer.validated_data.get("principals", False)
        core_members = serializer.validated_data.get("core_members", False)
        musicians = []
        if musician_id:
            musicians = add_musician_to_program(
                organization_id=request.organization.id,
                program_id=program_id,
                musician_id=musician_id,
            )
        elif principals or core_members:
            musicians = add_musicians_to_program(
                organization_id=request.organization.id,
                program_id=program_id,
                principals=principals,
                core_members=core_members,
            )
        else:
            musicians = get_musicians_for_program(
                organization_id=request.organization.id, program_id=program_id
            )
        response_data = [musician.model_dump(mode="json") for musician in musicians]
        return Response(response_data, status=status.HTTP_200_OK)

    def list(self, request, program_id, *args, **kwargs):
        musicians = get_musicians_for_program(request.organization.id, program_id)
        response_data = [musician.model_dump(mode="json") for musician in musicians]
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, program_id, program_musician_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        musicians = remove_musician_from_program(
            request.organization.id, program_id, program_musician_id
        )
        response_data = [musician.model_dump(mode="json") for musician in musicians]
        return Response(response_data, status=status.HTTP_200_OK)


class ProgramMusicianInstrumentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def get_serializer_class(self, data):
        return ProgramMusicianInstrumentSerializer(data=data)

    @transaction.atomic
    def update(self, request, program_id, program_musician_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instrument = serializer.validated_data.get("instrument")
        musicians = add_program_musician_instrument(
            request.organization.id, program_id, program_musician_id, instrument
        )
        response_data = [musician.model_dump(mode="json") for musician in musicians]
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, program_id, program_musician_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instrument = serializer.validated_data.get("instrument")
        musicians = remove_program_musician_instrument(
            request.organization.id, program_id, program_musician_id, instrument
        )
        response_data = [musician.model_dump(mode="json") for musician in musicians]
        return Response(response_data, status=status.HTTP_200_OK)


class ProgramChecklistViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def get_serializer_class(self, data):
        return ProgramChecklistPatchSerializer(data=data)

    def retrieve(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        checklist = get_program_checklist(request.organization.id, program_id)
        response_data = checklist.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def partial_update(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            program_checklist = update_program_checklist(
                organization_id=request.organization.id,
                program_id=program_id,
                user_id=request.user.id,
                **serializer.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_data = program_checklist.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)
