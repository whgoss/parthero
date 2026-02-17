from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from core.api.permissions import IsInOrganization
from core.models.programs import Program
from core.services.assignments import get_program_assignments_status


class ProgramAssignmentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsInOrganization]

    def list(self, request, program_id, *args, **kwargs):
        Program.objects.get(id=program_id, organization_id=request.organization.id)
        payload = get_program_assignments_status(
            organization_id=request.organization.id,
            program_id=program_id,
        )
        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)
