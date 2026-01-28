import pytz
from datetime import datetime
from typing import Optional, List
from django.db import transaction
from django.db.models import Min, F
from django.utils import timezone
from core.dtos.programs import ProgramDTO
from core.enum.status import ProgramStatus
from core.models.organizations import Organization
from core.models.programs import Program, ProgramPerformance


@transaction.atomic
def create_program(
    organization_id: str,
    name: str,
    status: Optional[ProgramStatus] = ProgramStatus.CREATED,
    performance_dates: Optional[List[datetime]] = None,
) -> ProgramDTO:
    organization = Organization.objects.get(id=organization_id)
    program = Program(
        organization_id=organization.id,
        name=name,
        status=status.value,
    )
    program.save()

    for performance_date in performance_dates or []:
        # Convert from the organization's time zone to UTC
        # TODO: Consider different timezones per performance?
        target_timezone = pytz.timezone(organization.timezone)
        if timezone.is_naive(performance_date):
            performance_date = target_timezone.localize(performance_date)
        performance_date = performance_date.astimezone(pytz.UTC)
        program_performance = ProgramPerformance(
            program_id=program.id, date=performance_date
        )
        program_performance.save()
    return ProgramDTO.from_model(program)


def get_program(piece_id: str) -> ProgramDTO:
    program = Program.objects.get(id=piece_id)
    return ProgramDTO.from_model(program)


def get_programs(organization_id: str) -> List[ProgramDTO]:
    programs = (
        Program.objects.filter(organization_id=organization_id)
        .annotate(first_performance=Min("performances__date"))
        .order_by(F("first_performance").asc(nulls_last=True))
    )
    return ProgramDTO.from_models(programs)
