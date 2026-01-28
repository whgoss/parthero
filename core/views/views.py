import json
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from core.forms.music import PieceForm
from core.forms.programs import ProgramForm, PerformanceFormSet
from core.services.music import (
    create_piece,
    get_piece,
    get_parts,
    get_pieces,
    get_part_assets,
    get_part_asset,
)
from core.services.programs import create_program, get_program, get_programs
from core.services.domo import search_for_piece
from core.services.s3 import create_download_url


@login_required
def home(request):
    return render(request, "home.html")


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


@require_GET
@login_required
def get_parts_view(request, piece_id):
    parts = get_parts(piece_id)
    part_assets = get_part_assets(piece_id)

    # Find all parts that don't have an asset
    completed_parts = []
    for part_asset in part_assets:
        if part_asset.parts is not None:
            for part in part_asset.parts:
                completed_parts.append(part)
    missing_parts = []
    for part in parts:
        if part not in completed_parts:
            missing_parts.append(part)

    # Collect all unassigned part assets
    unassigned_part_assets = []
    for part_asset in part_assets:
        if not part_asset.parts:
            unassigned_part_assets.append(part_asset)

    context = {
        "piece_id": piece_id,
        "part_assets": part_assets,
        "missing_parts": missing_parts,
        "unassigned_part_assets": unassigned_part_assets,
        "part_options_json": json.dumps(
            [{"value": part.display_name, "id": part.id} for part in parts]
        ),
    }

    return render(request, "partials/parts.html", context)


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
    part_asset = get_part_asset(part_asset_id)
    if not part_asset:
        return HttpResponseNotFound("Unable to find asset")

    download_url = create_download_url(
        str(request.organization.id), part_asset.file_key
    )
    return redirect(download_url)


@login_required
def get_program_view(request, program_id):
    program = get_program(program_id)
    context = {
        "program": program,
    }
    return render(request, "program.html", context)


@login_required
def get_programs_view(request):
    programs = get_programs(request.organization.id)
    context = {
        "programs": programs,
    }
    return render(request, "programs.html", context)


@login_required
def create_program_view(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        formset = PerformanceFormSet(request.POST, prefix="perf")

        if form.is_valid() and formset.is_valid():
            performance_dates = []
            for subform in formset:
                performance_dates.append(subform.cleaned_data["date"])

            create_program(
                organization_id=str(request.organization.id),
                name=form.data["name"],
                performance_dates=performance_dates,
            )

            return redirect("programs")
    else:
        form = ProgramForm(organization_id=request.organization.id)
        formset = PerformanceFormSet(prefix="perf")
    context = {"form": form, "formset": formset}
    return render(request, "create_program.html", context)


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
