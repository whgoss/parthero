from enum import Enum


class UploadStatus(Enum):
    PENDING = "Pending"
    FAILED = "Failed"
    UPLOADED = "Uploaded"
    ABORTED = "Aborted"
    NONE = "None"

    def choices():
        return [(status.value, status.value) for status in UploadStatus]


class ProgramStatus(Enum):
    CREATED = "Created"
    PIECES = "Pieces"
    ROSTER = "Roster"
    READY = "Ready"
    PUBLISHED = "Published"

    def choices():
        return [(status.value, status.value) for status in ProgramStatus]
