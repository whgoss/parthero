from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from core.api.serializers import PartCreateSerializer
from core.services.music import create_part
from core.api.permissions import IsInOrganization


class PartViewSet(APIView):
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
