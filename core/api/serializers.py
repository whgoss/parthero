from rest_framework import serializers
from pydantic import ValidationError as PydanticValidationError
from core.dtos.music import PartDTO
from core.enum.status import UploadStatus
from core.enum.music import PartAssetType
from core.enum.instruments import InstrumentEnum
from core.utils import EnumChoiceField


class PartAssetCreateSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    asset_type = EnumChoiceField(PartAssetType, default=PartAssetType.CLEAN)

    def validate_filename(self, value):
        # TODO: ensure extension is allowed, etc.
        return value


class PartAssetPatchSerializer(serializers.Serializer):
    status = EnumChoiceField(UploadStatus, required=False)
    part_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )


class PartCreateSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)

    def validate_filename(self, value):
        # TODO: ensure extension is allowed, etc.
        return value


class PartPatchSerializer(serializers.Serializer):
    instrument_sections = serializers.ListField(
        child=EnumChoiceField(InstrumentEnum),
        required=False,
    )


class ProgramMusicianCreateSerializer(serializers.Serializer):
    musician_id = serializers.CharField(required=True)


class ProgramMusicianInstrumentSerializer(serializers.Serializer):
    instrument = EnumChoiceField(InstrumentEnum, required=True)


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
