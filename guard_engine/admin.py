from django.contrib import admin
from guard_engine.models import SecuredFile, SecuredUrl
from .admin_forms import SecuredUrlForm, SecuredFileForm


admin.AdminSite.site_header = 'File guard - admin panel'
admin.AdminSite.index_title = 'Admin panel'
admin.AdminSite.site_url = '/'
admin.site.empty_value_display = '-'


@admin.register(SecuredUrl)
class SecuredUrlFileAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource_route', 'url_route', 'expire_ts')
    search_fields = ['user', 'resource_route', 'url_route']
    list_filter = ('expire_ts',)
    autocomplete_fields = ['user', ]
    form = SecuredUrlForm

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return super().get_queryset(request).filter(user=request.user)
        return super().get_queryset(request)

    def get_form(self, request, obj=None, change=False, **kwargs):
        if not request.user.is_superuser:
            self.fields = ('password', )
        return super().get_form(request, obj, **kwargs)


@admin.register(SecuredFile)
class SecuredFileAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource_route', 'persisted_file', 'expire_ts')
    search_fields = ['user', 'resource_route', 'persisted_file__name']
    list_filter = ('expire_ts',)
    autocomplete_fields = ['user', ]
    form = SecuredFileForm

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return super().get_queryset(request).filter(user=request.user)
        return super().get_queryset(request)

    def get_form(self, request, obj=None, change=False, **kwargs):
        if not request.user.is_superuser:
            self.fields = ('name', 'phone_number', 'email', 'contact_channels')
        return super().get_form(request, obj, **kwargs)

