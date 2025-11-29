from rest_framework import serializers
from core.dtos.music import PartDTO
from pydantic import ValidationError as PydanticValidationError


class PartCreateSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)

    # if you want, you can do extra validation here
    def validate_filename(self, value):
        # e.g. ensure extension is allowed, etc.
        return value


class PartDTOWrapperSerializer(serializers.Serializer):
    def validate(self, attrs):
        # attrs is empty because we’re not declaring explicit fields,
        # so use the raw body instead:
        raw_data = self.initial_data

        try:
            dto = PartDTO(**raw_data)
        except PydanticValidationError as e:
            raise serializers.ValidationError(e.errors())

        attrs["dto"] = dto
        return attrs
