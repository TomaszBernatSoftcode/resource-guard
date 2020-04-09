from rest_framework import serializers
from guard_engine.models import SecuredFile


class FileRouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecuredFile
        fields = ('persisted_file',)


class FileResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecuredFile
        exclude = ['file_size']

