from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from core.forms.music import PieceForm
from core.services.music import (
    create_piece,
    create_edition,
    get_piece_by_id,
    get_parts,
    get_edition,
    get_editions_for_piece,
    get_editions,
    get_editions_count,
)
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
        edition_name = form.data["edition_name"]
        composer = form.data["composer"]
        arranger = form.data["arranger"]
        instrumentation = form.data["instrumentation"]
        duration = form.data["duration"]
        organization_id = request.organization.id
        piece = create_piece(organization_id, title, composer, arranger)
        edition = create_edition(piece.id, edition_name, instrumentation, duration)
        return redirect(f"/piece/{piece.id}/edition/{edition.id}/")
    else:
        form = PieceForm(
            organization_id=request.organization.id,
        )
    context = {"form": form}
    return render(request, "create_piece.html", context)


@login_required
def upload_parts(request, piece_id):
    piece = get_piece_by_id(request.organization.id, piece_id)
    context = {
        "piece": piece,
    }
    return render(request, "upload_parts.html", context)


@login_required
def piece(request, piece_id):
    piece = get_piece_by_id(request.organization.id, piece_id)
    editions = get_editions_for_piece(piece_id)
    return redirect(f"/piece/{piece.id}/edition/{editions[0].id}")


@login_required
def pieces(request):
    editions = get_editions(request.organization.id)
    context = {
        "editions": editions,
        "pieces_count": get_editions_count(request.organization.id),
    }
    return render(request, "pieces.html", context)


@login_required
def edition(request, piece_id, edition_id):
    edition = get_edition(edition_id)
    editions = get_editions_for_piece(piece_id)
    parts = get_parts(edition_id)
    instrumentation = parse_instrumentation(edition.instrumentation)
    context = {
        "parts": parts,
        "edition": edition,
        "editions": editions,
        "instrumentation": instrumentation,
    }
    return render(request, "edition.html", context)


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
