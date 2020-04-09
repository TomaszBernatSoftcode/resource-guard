from django import forms
from .models import SecuredUrl, SecuredFile


class SecuredUrlForm(forms.ModelForm):
    class Meta:
        model = SecuredUrl
        fields = [
            'user', 'resource_route', 'password', 'creation_date',
            'expire_ts', 'visit_counter', 'latest_user_agent', 'url_route'
        ]
        widgets = {'password': forms.PasswordInput()}


class SecuredFileForm(forms.ModelForm):
    class Meta:
        model = SecuredFile
        fields = [
            'user', 'resource_route', 'password', 'creation_date',
            'expire_ts', 'visit_counter', 'latest_user_agent', 'file_size', 'persisted_file'
        ]
        widgets = {'password': forms.PasswordInput()}
