from django.http import Http404
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from core.enum.notifications import MagicLinkType
from core.services.assignments import assign_program_part, get_assignment_payload
from core.services.magic_links import (
    get_valid_magic_link,
    mark_magic_link_accessed,
    mark_magic_link_completed,
)


def _get_assignment_magic_link(token: str):
    try:
        magic_link = get_valid_magic_link(
            token=token, link_type=MagicLinkType.ASSIGNMENT
        )
    except Exception as exc:
        raise Http404("Magic link is invalid or expired.") from exc

    if not magic_link.program_id or not magic_link.musician_id:
        raise Http404("Magic link is invalid.")

    return magic_link


class MagicAssignmentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def retrieve(self, request, token, *args, **kwargs):
        magic_link = _get_assignment_magic_link(token)
        mark_magic_link_accessed(magic_link)
        payload = get_assignment_payload(
            program_id=str(magic_link.program_id),
            principal_musician_id=str(magic_link.musician_id),
        )
        return Response(payload.model_dump(mode="json"), status=status.HTTP_200_OK)


class MagicAssignmentPartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def partial_update(self, request, token, part_id, *args, **kwargs):
        magic_link = _get_assignment_magic_link(token)
        mark_magic_link_accessed(magic_link)

        musician_id = request.data.get("musician_id")
        if musician_id is not None and not isinstance(musician_id, str):
            return Response(
                {"detail": "musician_id must be a string or null."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            updated = assign_program_part(
                program_id=str(magic_link.program_id),
                principal_musician_id=str(magic_link.musician_id),
                part_id=part_id,
                musician_id=musician_id,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(updated.model_dump(mode="json"), status=status.HTTP_200_OK)


class MagicAssignmentConfirmViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, token, *args, **kwargs):
        magic_link = _get_assignment_magic_link(token)
        mark_magic_link_accessed(magic_link)

        payload = get_assignment_payload(
            program_id=str(magic_link.program_id),
            principal_musician_id=str(magic_link.musician_id),
        )
        if not payload.all_assigned:
            return Response(
                {"detail": "All parts must be assigned before confirming."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mark_magic_link_completed(magic_link)
        return Response({"ok": True}, status=status.HTTP_200_OK)
