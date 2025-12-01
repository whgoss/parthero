from enum import Enum


class UploadStatus(Enum):
    PENDING = "Pending"
    FAILED = "Failed"
    UPLOADED = "Uploaded"
    ABORTED = "Aborted"

    def choices():
        return [(status.value, status.value) for status in UploadStatus]
