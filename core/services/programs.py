from typing import Optional
from core.dtos.programs import ProgramDTO
from core.enum.status import ProgramStatus
from core.models.organizations import Organization
from core.models.programs import Program


def create_program(
    organization_id: str,
    title: str,
    status: Optional[ProgramStatus] = ProgramStatus.DRAFT,
) -> ProgramDTO:
    organization = Organization.objects.get(id=organization_id)
    program = Program(
        organization_id=organization.id,
        title=title,
        status=status,
    )
    program.save()
    return ProgramDTO.from_model(program)
