from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from core.forms.music import PieceForm
from core.services.music import (
    create_piece,
    get_piece,
    get_pieces,
    get_part_asset,
)
from core.services.organizations import get_setup_checklist
from core.services.domo import search_for_piece
from core.services.s3 import create_download_url
from parthero.settings import DOWNLOAD_URL_EXPIRATION_SECONDS


@login_required
def home(request):
    setup_checklist = get_setup_checklist(request.organization.id)
    context = {
        "setup_checklist": setup_checklist,
    }
    return render(request, "home.html", context)


@login_required
def create_piece_view(request):
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
        return redirect(f"/pieces/{piece.id}/")
    else:
        domo_id = request.GET.get("domo_id", None)
        form = PieceForm(
            organization_id=request.organization.id,
            domo_id=domo_id,
        )
    context = {"form": form}
    return render(request, "create_piece.html", context)


@login_required
def get_piece_view(request, piece_id):
    piece = get_piece(request.organization.id, piece_id)
    context = {
        "piece": piece,
        "instrumentation": piece.instrumentation,
    }

    return render(request, "piece.html", context)


@login_required
def get_pieces_view(request):
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


def download_part_asset(request, piece_id, part_asset_id):
    part_asset = get_part_asset(request.organization.id, part_asset_id)
    if not part_asset:
        return HttpResponseNotFound("Unable to find asset")

    download_url = create_download_url(
        organization_id=request.organization.id,
        file_key=part_asset.file_key,
        expiration=DOWNLOAD_URL_EXPIRATION_SECONDS,
    )
    return redirect(download_url)


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
