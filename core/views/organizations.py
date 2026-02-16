import io
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from core.enum.instruments import InstrumentEnum
from core.services.organizations import (
    create_musician,
    get_roster,
    get_musician,
    update_musician,
)
from core.services.files import upload_roster as upload_roster_file
from core.models.users import UserOrganization
from core.forms.musicians import MusicianForm


@login_required
def upload_roster(request):
    uploaded_file = request.FILES.get("roster_csv")

    if uploaded_file:
        file_data = uploaded_file.read().decode("utf-8")
        io_string = io.StringIO(file_data)
        upload_roster_file(io_string, request.organization.id)

    return redirect("/roster")


@login_required
def roster(request):
    musicians = get_roster(request.organization.id)
    context = {"musicians": musicians}
    return render(request, "roster.html", context)


@login_required
def musician(request, musician_id: str | None = None):
    musician = get_musician(request.organization.id, musician_id)
    original_email = musician.email if musician else None

    if request.method == "POST":
        form = MusicianForm(
            request.POST,
            original_email=original_email,
            organization_id=request.organization.id,
        )
        if form.is_valid():
            if musician:
                musician = update_musician(
                    organization_id=request.organization.id,
                    musician_id=musician.id,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    email=form.cleaned_data["email"],
                    principal=form.cleaned_data.get("principal", False),
                    core_member=form.cleaned_data.get("core_member", False),
                    instruments=form.cleaned_data.get("instruments"),
                )
                messages.success(
                    request,
                    f"{musician.first_name} {musician.last_name} was edited successfully.",
                    extra_tags="musician",
                )
            else:
                musician = create_musician(
                    organization_id=request.organization.id,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    email=form.cleaned_data["email"],
                    principal=form.cleaned_data.get("principal", False),
                    core_member=form.cleaned_data.get("core_member", False),
                    instruments=None,
                )
                messages.success(
                    request,
                    f"{musician.first_name} {musician.last_name} was created successfully.",
                    extra_tags="musician",
                )

            response = redirect(f"/musicians/{musician.id}")
            return response
    else:
        form = MusicianForm(
            initial={
                "first_name": musician.first_name if musician else None,
                "last_name": musician.last_name if musician else None,
                "email": musician.email if musician else None,
                "principal": musician.principal if musician else None,
                "core_member": musician.core_member if musician else None,
            },
            original_email=original_email,
            organization_id=request.organization.id,
        )

    instruments = []
    if musician:
        for instrument in musician.instruments:
            instruments.append(instrument.instrument.value)

    context = {
        "musician": musician,
        "form": form,
        "instruments": json.dumps(instruments),
        "instrument_options": InstrumentEnum.values(),
    }
    return render(request, "musician.html", context)


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
