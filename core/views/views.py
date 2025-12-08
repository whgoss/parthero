from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from core.services.music import (
    create_piece,
    get_piece_by_id,
    get_pieces,
    get_pieces_count,
    get_parts,
)
from core.models.users import UserOrganization


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def create_new_piece(request):
    if request.method == "POST":
        title = request.POST.get("title")
        composer = request.POST.get("composer")
        organization_id = request.organization.id
        piece = create_piece(title, composer, organization_id)
        return redirect(f"/piece/{piece.id}/")
    return render(request, "create_piece.html")


@login_required
def upload_parts(request, piece_id):
    piece = get_piece_by_id(piece_id, request.organization.id)
    context = {
        "piece": piece,
    }
    return render(request, "upload_parts.html", context)


@login_required
def piece(request, piece_id):
    piece = get_piece_by_id(piece_id, request.organization.id)
    parts = get_parts(piece_id)
    context = {
        "piece": piece,
        "parts": parts,
    }
    return render(request, "piece.html", context)


@login_required
def pieces(request):
    pieces = get_pieces(request.organization.id)
    context = {
        "pieces": pieces,
        "pieces_count": get_pieces_count(request.organization.id),
    }
    return render(request, "pieces.html", context)


@login_required
def roster(request):
    context = {}
    return render(request, "roster.html", context)


@login_required
def programs(request):
    context = {}
    return render(request, "programs.html", context)


@login_required
def switch_organization(request, organization_id):
    membership = UserOrganization.objects.filter(
        user=request.user, organization_id=organization_id
    ).first()

    if not membership:
        return HttpResponseForbidden("You are not a member of this organization.")

    request.session["organization_id"] = organization_id
    next_url = request.GET.get("next") or "/"
    return redirect(next_url)


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
