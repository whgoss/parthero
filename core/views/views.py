from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from core.forms.music import PieceForm
from core.services.music import (
    create_piece,
    get_piece,
    get_parts,
    get_pieces,
)
from core.services.domo import search_for_piece
from core.services.instrumentation import parse_instrumentation


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def create_new_piece(request):
    if request.method == "POST":
        form = PieceForm(
            request.POST,
            organization_id=request.organization.id,
        )
        title = form.data["title"]
        composer = form.data["composer"]
        instrumentation = form.data["instrumentation"]
        duration = form.data["duration"]
        organization_id = request.organization.id
        domo_id = form.data.get("domo_id", None)
        composer_domo_id = form.data.get("composer_domo_id", None)
        piece = create_piece(
            organization_id,
            title,
            composer,
            instrumentation,
            duration,
            domo_id,
            composer_domo_id,
        )
        return redirect(f"/piece/{piece.id}/")
    else:
        domo_id = request.GET.get("domo_id", None)
        form = PieceForm(
            organization_id=request.organization.id,
            domo_id=domo_id,
        )
    context = {"form": form}
    return render(request, "create_piece.html", context)


@login_required
def piece(request, piece_id):
    piece = get_piece(request.organization.id, piece_id)
    parts = get_parts(piece_id)
    instrumentation = parse_instrumentation(piece.instrumentation)
    part_instruments = []
    for part in parts:
        for part_instrument in part.part_instruments:
            part_instruments.append(part_instrument.instrument_section.name)

    missing_parts = []
    for part_slot in instrumentation:
        if any(
            section not in part_instruments for section in part_slot.instrument_sections
        ):
            missing_parts.append(part_slot)

    context = {
        "piece": piece,
        "parts": parts,
        "instrumentation": instrumentation,
        "missing_parts": missing_parts,
        "missing_parts_count": len(missing_parts),
    }

    return render(request, "piece.html", context)


@login_required
def pieces(request):
    pieces = get_pieces(request.organization.id)
    context = {
        "pieces": pieces,
        "piece_count": len(pieces),
    }
    return render(request, "pieces.html", context)


@login_required
def select_piece(request):
    return render(request, "select_piece.html")


@require_POST
@login_required
def search(request):
    title = request.POST.get("title", None)
    composer = request.POST.get("composer", None)

    results = []
    if title or composer:
        results = search_for_piece(title, composer)

    context = {
        "search_results": results,
    }
    return render(request, "partials/search_results.html", context)


# @login_required
# def edition(request, piece_id, edition_id):
#     edition = get_edition(edition_id)
#     editions = get_editions_for_piece(piece_id)
#     parts = get_parts(edition_id)
#     instrumentation = parse_instrumentation(edition.instrumentation)

#     instrumentation = parse_instrumentation(edition.instrumentation)
#     part_instruments = []
#     for part in parts:
#         for part_instrument in part.part_instruments:
#             part_instruments.append(part_instrument.instrument_section.name)

#     missing_parts = []
#     for part_slot in instrumentation:
#         for instrument_section in part_slot.instrument_sections:
#             if instrument_section not in part_instruments:
#                 missing_parts.append(part_slot)

#     # uploaded_sections = {
#     #     part_instrument.instrument_section
#     #     for part in parts
#     #     for part_instrument in part.part_instruments
#     # }

#     # missing_parts = [
#     #     part_slot
#     #     for part_slot in instrumentation
#     #     if set(part_slot.instrument_sections).isdisjoint(uploaded_sections)
#     # ]

#     context = {
#         "parts": parts,
#         "edition": edition,
#         "editions": editions,
#         "instrumentation": instrumentation,
#         "missing_parts": missing_parts,
#         "missing_parts_count": len(missing_parts),
#     }
#     return render(request, "edition.html", context)


@login_required
def programs(request):
    context = {}
    return render(request, "programs.html", context)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.GET.get("next") or "/"
            return redirect(next_url)
        else:
            # you can use messages, or just pass an error to the template
            return render(
                request, "login.html", {"error": "Invalid username or password."}
            )

    return render(request, "login.html")
