from core.dtos.base import BaseDTO
from core.enum.notifications import (
    NotificationMethod,
    NotificationStatus,
    NotificationType,
)
from core.models.notifications import Notification
from core.dtos.organizations import MusicianDTO
from typing import Optional


class NotificationDTO(BaseDTO):
    organization_id: str
    program_id: str
    recipient: Optional[MusicianDTO] = None
    type: NotificationType
    status: NotificationStatus
    method: NotificationMethod

    @classmethod
    def from_model(cls, model: Notification):
        return cls(
            id=str(model.id),
            organization_id=str(model.program.organization.id),
            program_id=str(model.program.id),
            recipient=MusicianDTO.from_model(model.recipient)
            if model.recipient
            else None,
            type=NotificationType(model.type),
            status=NotificationStatus(model.status),
            method=NotificationMethod(model.method),
        )
