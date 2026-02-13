from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice.value, choice.value) for choice in cls]

    @classmethod
    def values(cls):
        return [choice.value for choice in cls]
