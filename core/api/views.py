from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from core.api.serializers import (
    PartCreateSerializer,
    PartDTOWrapperSerializer,
)
from core.services.music import (
    create_part,
    update_part,
    covered_slots_for_part,
    get_edition,
    get_instrument_section,
)
from core.services.instrumentation import parse_instrumentation
from core.api.permissions import IsInOrganization
from core.dtos.music import PartDTO
from core.models.music import PartInstrument


class PartCreateViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    @transaction.atomic
    def post(self, request, edition_id, *args, **kwargs):
        serializer = PartCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. Grab serialized data from request
        filename = serializer.validated_data["filename"]

        # 2. Pass to service layer to create part
        part = create_part(edition_id, filename)

        # 3. Determine covered part slot for part
        edition = get_edition(edition_id)
        instrumentation = parse_instrumentation(edition.instrumentation)
        part_slots = covered_slots_for_part(part.id, instrumentation)
        for part_slot in part_slots:
            for instrument_section in part_slot.instrument_sections:
                instrument_section_model = get_instrument_section(instrument_section)
                part_instrument = PartInstrument(
                    part_id=part.id,
                    instrument_section_id=instrument_section_model.id,
                    number=part_slot.number if part_slot.number else None,
                )
                part_instrument.save()

        response_data = part.model_dump(mode="json")
        return Response(response_data, status=status.HTTP_200_OK)


class PartViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def put(self, request, edition_id, part_id, *args, **kwargs):
        serializer = PartDTOWrapperSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        part: PartDTO = serializer.validated_data["dto"]

        # Enforce ID + org from trusted context, not the client
        part = part.model_copy(
            update={
                "id": part_id,
                "edition_id": edition_id,
            }
        )

        updated = update_part(part)
        return Response(updated.model_dump(mode="json"), status=status.HTTP_200_OK)
