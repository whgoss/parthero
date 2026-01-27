from core.dtos.base import BaseDTO
from core.enum.status import ProgramStatus
from core.models.programs import Program


class ProgramDTO(BaseDTO):
    organization_id: str
    title: str
    status: ProgramStatus = ProgramStatus.DRAFT

    @classmethod
    def from_model(
        cls,
        model: Program,
    ):
        return cls(
            id=str(model.id),
            organization_id=model.organization.id,
            title=model.title,
            status=ProgramStatus(model.status),
        )
