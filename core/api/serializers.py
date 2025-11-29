from rest_framework import serializers


class PartCreateSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)

    # if you want, you can do extra validation here
    def validate_filename(self, value):
        # e.g. ensure extension is allowed, etc.
        return value
