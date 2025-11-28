from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from core.services.music import get_pieces_for_organization
from core.models.users import UserOrganization


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def pieces(request):
    pieces = get_pieces_for_organization(request.organization.id)
    context = {
        "pieces": pieces,
    }
    return render(request, "pieces.html", context)


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
