from core.enum.base import BaseEnum


class NotificationMethod(BaseEnum):
    EMAIL = "Email"


class NotificationType(BaseEnum):
    ASSIGNMENT = "Assignment"
    PART_DELIVERY = "Part Delivery"


class NotificationStatus(BaseEnum):
    CREATED = "Created"
    SENT = "Sent"
    FAILED = "Failed"


class MagicLinkType(BaseEnum):
    ASSIGNMENT = "Assignment"
