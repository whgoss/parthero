from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from core.forms.programs import ProgramForm, PerformanceFormSet
from core.services.programs import (
    create_program,
    get_program,
    get_programs,
    get_pieces_for_program,
)
from core.enum.instruments import InstrumentEnum


@login_required
def get_program_view(request, program_id):
    program = get_program(program_id)
    pieces = get_pieces_for_program(program_id)
    context = {
        "program": program,
        "pieces": pieces,
        "instrument_options": InstrumentEnum.values(),
    }
    return render(request, "program.html", context)


@login_required
def get_programs_view(request):
    upcoming_program = None
    upcoming_pieces = []
    programs = get_programs(request.organization.id)
    if programs:
        upcoming_program = programs[0]
        upcoming_pieces = get_pieces_for_program(upcoming_program.id)
    context = {
        "programs": programs,
        "upcoming_program": upcoming_program,
        "upcoming_pieces": upcoming_pieces,
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
                organization_id=request.organization.id,
                name=form.data["name"],
                performance_dates=performance_dates,
            )

            return redirect("programs")
    else:
        form = ProgramForm(organization_id=request.organization.id)
        formset = PerformanceFormSet(prefix="perf")
    context = {"form": form, "formset": formset}
    return render(request, "create_program.html", context)
