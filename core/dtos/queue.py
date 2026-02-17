from pydantic import BaseModel

from core.enum.notifications import NotificationType


class EmailQueuePayloadDTO(BaseModel):
    organization_id: str
    program_id: str
    musician_id: str
    notification_type: NotificationType
