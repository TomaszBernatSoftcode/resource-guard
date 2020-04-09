import datetime
import string
from uuid import uuid4
from random import choice, randint
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from api.serializers.file_route import FileRouteSerializer, FileResourceSerializer
from api.serializers.resource_password import ResourcePasswordDetailsSerializer
from api.serializers.url_route import UrlRouteSerializer, UrlResourceSerializer
from guard_engine.models import SecuredUrl, SecuredFile
from django.utils import timezone
from django.apps import apps
from django.conf import settings
from django.db.models import Sum


@api_view(['POST'])
def check_resource_password(request):
    serialized_request = ResourcePasswordDetailsSerializer(data=request.POST)
    if not serialized_request.is_valid():
        return Response(status=status.HTTP_403_FORBIDDEN)

    data = serialized_request.data
    source = apps.get_model('guard_engine', 'SecuredUrl' if data.get('resource_type') == 'urls' else 'SecuredFile')
    try:
        resource_object = source.objects.get(
            user__username=data.get('user_name'),
            resource_route='{user_name}/{resource_type}/{resource_uid}'.format(
                user_name=data.get('user_name'),
                resource_type=data.get('resource_type'),
                resource_uid=data.get('resource_uid')
            ),
            password=data.get('password')
        )
    except (SecuredUrl.DoesNotExist, SecuredFile.DoesNotExist) as e:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not resource_object.is_accessible():
        resource_object.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)

    serialized_resource = UrlRouteSerializer(resource_object) if data.get('resource_type') == 'urls' else FileRouteSerializer(resource_object)
    resource_object.visit_counter += 1
    resource_object.latest_user_agent = request.META['HTTP_USER_AGENT'][:64]
    resource_object.save()

    return Response(serialized_resource.data)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def secure_new_resource(request):
    requested_file = request.FILES
    requested_url = request.data

    if (not requested_file or 'persisted_file' not in requested_file) and not requested_url:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    resource = UrlRouteSerializer(data=requested_url) if requested_url and not requested_file else FileRouteSerializer(data=requested_file)
    if not resource.is_valid():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    creation_ts = timezone.now()

    if requested_file:
        file_size = resource.validated_data['persisted_file'].size
        created_files_size = SecuredFile.objects.filter(
            user=user, expire_ts__gte=creation_ts
        ).aggregate(files_size=Sum('file_size')).get('files_size')

        if file_size > settings.FILE_LIMIT_SIZE or created_files_size + file_size > settings.USER_FILES_LIMIT:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    else:
        links_number = SecuredUrl.objects.filter(user=user, expire_ts__gte=creation_ts).count()
        if links_number + 1 > settings.LINKS_LIMIT:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

    new_resource_data = {
        'user': user.id,
        'resource_route': "{user_name}/urls/{resource_uid}".format(
            user_name=user.username,
            resource_uid=uuid4().time_low
        ),
        'password': "".join(
            choice(string.ascii_letters + string.punctuation + string.digits) for i in range(randint(8, 16))
        ),
        'creation_date': creation_ts.date(),
        'expire_ts': creation_ts + datetime.timedelta(days=1),
        'visit_counter': 0,
        'latest_user_agent': request.META['HTTP_USER_AGENT'][:64]
    }

    if requested_file:
        new_resource_data['persisted_file'] = resource.validated_data['persisted_file']
        serialized_resource = FileResourceSerializer(data=new_resource_data)
    else:
        new_resource_data['url_route'] = resource.validated_data['url_route']
        serialized_resource = UrlResourceSerializer(data=new_resource_data)

    if not serialized_resource.is_valid():
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    created_resource = serialized_resource.save()
    return Response({
        'http_route': '{domain}/{route}'.format(
            domain=request.META['HTTP_HOST'], route=created_resource.resource_route
        ),
        'password': created_resource.password
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def details_of_resources(request):
    request_user = request.user
    verification_ts = timezone.now()
    SecuredUrl.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()
    SecuredFile.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()

    unique_creation_dates = set(
        list(SecuredUrl.objects.distinct('creation_date').values_list('creation_date', flat=True)) +
        list(SecuredFile.objects.distinct('creation_date').values_list('creation_date', flat=True))
    )

    resources_details = {}
    for creation_date in unique_creation_dates:
        date_key = creation_date.strftime('%Y-%m-%d')
        resources_details[date_key] = {
            'files': SecuredFile.objects.filter(creation_date=date_key, visit_counter__gte=1).count(),
            'links': SecuredUrl.objects.filter(creation_date=date_key, visit_counter__gte=1).count()
        }
    if not resources_details:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(resources_details)
