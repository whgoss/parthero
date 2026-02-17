from core.enum.base import BaseEnum


class UploadStatus(BaseEnum):
    PENDING = "Pending"
    FAILED = "Failed"
    UPLOADED = "Uploaded"
    ABORTED = "Aborted"
    NONE = "None"
