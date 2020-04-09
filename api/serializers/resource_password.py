from rest_framework import serializers


class ResourcePasswordDetailsSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=256)
    resource_type = serializers.CharField(max_length=5, min_length=4)
    resource_uid = serializers.CharField(max_length=32)
    password = serializers.CharField(max_length=32)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
