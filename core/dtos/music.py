from typing import Optional
from datetime import timedelta
from core.dtos.base import BaseDTO
from core.models.music import Piece


class PieceDTO(BaseDTO):
    title: str
    composer: str
    organization_id: str
    arranger: Optional[str] = None
    duration: Optional[timedelta] = None

    @classmethod
    def from_model(cls, model: Piece):
        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization_id=str(model.organization.id),
            arranger=model.arranger,
            duration=model.duration,
        )


class PartDTO(BaseDTO):
    title: str
    composer: str
    organization_id: str
    arranger: Optional[str] = None
    duration: Optional[timedelta] = None

    @classmethod
    def from_model(cls, model: Piece):
        return cls(
            id=str(model.id),
            title=model.title,
            composer=model.composer,
            organization_id=str(model.organization.id),
            arranger=model.arranger,
            duration=model.duration,
        )
