from enum import Enum


class UploadStatus(Enum):
    PENDING = "Pending"
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"

    def choices():
        return [(status.value, status.value) for status in UploadStatus]
