from django.urls import path
from api.views import check_resource_password, secure_new_resource, details_of_resources


urlpatterns = [
    path('check-resource-password', check_resource_password, name='check_resource_password'),
    path('secure-resource', secure_new_resource, name='secure_new_resource'),
    path('resources-details', details_of_resources, name='details_of_resources')
]
