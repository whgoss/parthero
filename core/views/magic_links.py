from django.http import Http404
from django.shortcuts import render

from core.enum.notifications import MagicLinkType
from core.services.assignments import get_assignment_payload
from core.services.magic_links import (
    get_valid_magic_link,
    mark_magic_link_accessed,
)


def _get_assignment_magic_link(token: str):
    try:
        magic_link = get_valid_magic_link(
            token=token, link_type=MagicLinkType.ASSIGNMENT
        )
    except Exception:
        raise Http404("Magic link is invalid or expired.")
    if not magic_link.program_id or not magic_link.musician_id:
        raise Http404("Magic link is invalid.")
    return magic_link


def assignment_magic_link_view(request, token: str):
    magic_link = _get_assignment_magic_link(token)
    mark_magic_link_accessed(magic_link)

    payload = get_assignment_payload(
        program_id=str(magic_link.program_id),
        principal_musician_id=str(magic_link.musician_id),
    )
    context = {
        "magic_token": token,
        "program": magic_link.program,
        "musician": magic_link.musician,
        "payload": payload.model_dump(mode="json"),
    }
    return render(request, "magic_assignments.html", context)
