from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from guard_engine.views import SecuredUrlCreate, SecuredFileCreate, user_resources, resource_verifier, resource_details, user_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    # auth
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('logout', user_logout, name='logout'),
    # app
    path('', user_resources, name='user_resources'),
    path('secure-url', SecuredUrlCreate.as_view(), name='secure_url'),
    path('secure-file', SecuredFileCreate.as_view(), name='secure_file'),
    path('<str:resource_type>/<int:resource_id>/details', resource_details, name='resource_details'),
    path('<str:user_name>/<str:resource_type>/<str:resource_uid>', resource_verifier, name='resource_verifier'),
    # api
    path('api/', include('api.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
