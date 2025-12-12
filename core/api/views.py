from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from core.api.serializers import PartCreateSerializer, PartDTOWrapperSerializer
from core.services.music import create_part
from core.api.permissions import IsInOrganization
from core.dtos.music import PartDTO
from core.services.music import update_part


class PartCreateViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def post(self, request, piece_id, *args, **kwargs):
        serializer = PartCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. Grab serialized data from request
        filename = serializer.validated_data["filename"]

        # 2. Pass to service layer to create part
        part = create_part(piece_id, filename)
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
