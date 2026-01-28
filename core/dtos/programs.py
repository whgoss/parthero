from datetime import datetime
from typing import Optional, List
from core.dtos.base import BaseDTO
from core.enum.status import ProgramStatus
from core.models.programs import Program, ProgramPerformance


class ProgramDTO(BaseDTO):
    organization_id: str
    name: str
    status: ProgramStatus = ProgramStatus.CREATED
    piece_count: int
    performances: Optional[List["ProgramPerformanceDTO"]] = None

    @classmethod
    def from_model(
        cls,
        model: Program,
        piece_count: Optional[int] = None,
    ):
        if piece_count is None:
            piece_count = getattr(model, "piece_count", None)

        if piece_count is None:
            piece_count = model.pieces.count()

        return cls(
            id=str(model.id),
            organization_id=str(model.organization.id),
            name=model.name,
            status=ProgramStatus(model.status),
            performances=ProgramPerformanceDTO.from_models(model.performances.all()),
            piece_count=piece_count,
        )


class ProgramPerformanceDTO(BaseDTO):
    program_id: str
    date: datetime
    timezone: str

    @classmethod
    def from_model(cls, model: ProgramPerformance):
        return cls(
            id=str(model.id),
            program_id=str(model.program.id),
            date=model.date,
            timezone=model.timezone,
        )
