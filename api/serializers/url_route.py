from rest_framework import serializers
from guard_engine.models import SecuredUrl


class UrlRouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecuredUrl
        fields = ('url_route', )


class UrlResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecuredUrl
        fields = '__all__'
