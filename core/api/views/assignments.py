from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from core.api.serializers import ProgramAssignmentPartPatchSerializer
from core.api.permissions import IsInOrganization
from core.models.programs import Program
from core.services.assignments import (
    assign_program_part_by_librarian,
    get_program_assignments_status,
)


class ProgramAssignmentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        payload = get_program_assignments_status(
            organization_id=request.organization.id,
            program_id=program_id,
        )
        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)

    def partial_update(self, request, program_id, part_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        serializer = ProgramAssignmentPartPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = assign_program_part_by_librarian(
                organization_id=request.organization.id,
                program_id=program_id,
                part_id=part_id,
                musician_id=serializer.validated_data.get("musician_id"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)
