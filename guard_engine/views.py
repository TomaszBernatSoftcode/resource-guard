import datetime
import string
from random import choice, randint
from uuid import uuid4
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic.edit import CreateView
from guard_engine.models import SecuredUrl, SecuredFile
from django.apps import apps
from django.utils import timezone
from django.contrib.auth import logout
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP


@login_required
@require_GET
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
@require_GET
def user_resources(request):
    request_user = request.user
    verification_ts = timezone.now()
    SecuredUrl.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()
    SecuredFile.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()

    files_queryset = SecuredFile.objects.filter(user=request_user, expire_ts__gte=verification_ts)
    files_size = files_queryset.aggregate(files_size=Sum('file_size')).get('files_size')

    return render(request, 'pages/user_resources.html', {
        'urls': list(SecuredUrl.objects.filter(user=request_user, expire_ts__gte=verification_ts)),
        'files': list(files_queryset),
        'files_size': Decimal(files_size / settings.FILE_LIMIT_DIVISOR).quantize(
            Decimal('.0001'), rounding=ROUND_HALF_UP
        ) if files_size else 0,
        'urls_limit': settings.LINKS_LIMIT,
        'files_limit': Decimal(settings.USER_FILES_LIMIT / settings.FILE_LIMIT_DIVISOR).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    })


@login_required
@require_GET
def resource_verifier(request, user_name, resource_type, resource_uid):
    if (
        not isinstance(user_name, str) or
        len(user_name) < 2 or
        not isinstance(resource_type, str) or
        resource_type not in ['urls', 'files'] or
        not isinstance(resource_uid, str) or
        len(resource_uid) < 7
    ):
        return HttpResponseBadRequest

    source = apps.get_model('guard_engine', 'SecuredUrl' if resource_type == 'urls' else 'SecuredFile')
    try:
        resource = source.objects.get(
            user__username=user_name,
            resource_route='{}/{}/{}'.format(user_name, resource_type, resource_uid)
        )

    except (SecuredUrl.DoesNotExist, SecuredFile.DoesNotExist) as e:
        return HttpResponseNotFound()

    if resource.is_accessible():
        return render(request, 'pages/resource_verifier.html', {
            'source': 'securedurl' if resource_type == 'urls' else 'securedfile',
            'id': resource.id
        })

    resource.delete()
    return HttpResponseNotFound()


@login_required
@require_GET
def resource_details(request, resource_type, resource_id):
    if (
            not isinstance(resource_type, str) or
            resource_type not in ('urls', 'files') or
            not isinstance(resource_id, int) or
            resource_id <= 0
    ):
        return HttpResponseBadRequest()

    source = apps.get_model('guard_engine', 'SecuredUrl' if resource_type == 'urls' else 'SecuredFile')
    try:
        resource = source.objects.get(id=resource_id, user=request.user)
    except (SecuredUrl.DoesNotExist, SecuredFile.DoesNotExist) as e:
        return HttpResponseNotFound()

    if resource.is_accessible():
        return render(request, 'pages/resource_details.html', {
            'password': resource.password,
            'resource_route': resource.resource_route,
            'expire_ts': resource.expire_ts
        })

    resource.delete()
    return HttpResponseNotFound()


class SecuredUrlCreate(LoginRequiredMixin, CreateView):
    model = SecuredUrl
    fields = ['url_route']

    def get(self, request, *args, **kwargs):
        request_user = request.user
        verification_ts = timezone.now()
        SecuredUrl.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()

        links_number = SecuredUrl.objects.filter(user=request_user, expire_ts__gte=verification_ts).count()
        if links_number >= settings.LINKS_LIMIT:
            return redirect('user_resources')

        return super().get(request)

    def form_valid(self, form):
        request_user = self.request.user
        creation_ts = timezone.now()

        links_number = SecuredUrl.objects.filter(user=request_user, expire_ts__gte=creation_ts).count()
        if links_number + 1 > settings.LINKS_LIMIT:
            return redirect('secure_file')

        form.instance.user = request_user
        form.instance.resource_route = "{user_name}/urls/{resource_uid}".format(
            user_name=request_user.username,
            resource_uid=uuid4().time_low
        )
        form.instance.password = "".join(
            choice(string.ascii_letters + string.punctuation + string.digits) for i in range(randint(8, 16))
        )
        form.instance.creation_date = creation_ts.date()
        form.instance.expire_ts = creation_ts + datetime.timedelta(days=1)
        form.instance.latest_user_agent = self.request.META['HTTP_USER_AGENT'][:64]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'resource_details',
            kwargs={
                'resource_type': 'urls',
                'resource_id': self.object.id
            }
        )


class SecuredFileCreate(LoginRequiredMixin, CreateView):
    model = SecuredFile
    fields = ['persisted_file']

    def get(self, request, *args, **kwargs):
        request_user = request.user
        verification_ts = timezone.now()
        SecuredFile.objects.filter(user=request_user, expire_ts__lt=verification_ts).delete()

        files_size = SecuredFile.objects.filter(
            user=request_user, expire_ts__gte=verification_ts
        ).aggregate(files_size=Sum('file_size')).get('files_size')

        if files_size and files_size >= settings.USER_FILES_LIMIT:
            return redirect('user_resources')

        return super().get(request)

    def form_valid(self, form):
        request_user = self.request.user
        creation_ts = timezone.now()

        files_size = SecuredFile.objects.filter(
            user=request_user, expire_ts__gte=creation_ts
        ).aggregate(files_size=Sum('file_size')).get('files_size')
        received_file = form.instance.persisted_file

        if not received_file:
            return redirect('secure_file')
        if received_file.size > settings.FILE_LIMIT_SIZE:
            return redirect('secure_file')
        if files_size and ((files_size + received_file.size) > settings.USER_FILES_LIMIT):
            return redirect('secure_file')

        form.instance.user = request_user
        form.instance.resource_route = "{user_name}/files/{resource_uid}".format(
            user_name=request_user.username,
            resource_uid=uuid4().time_low
        )
        form.instance.password = "".join(
            choice(string.ascii_letters + string.punctuation + string.digits) for i in range(randint(8, 16))
        )
        form.instance.creation_date = creation_ts.date()
        form.instance.expire_ts = creation_ts + datetime.timedelta(days=1)
        form.instance.latest_user_agent = self.request.META['HTTP_USER_AGENT'][:64]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'resource_details',
            kwargs={
                'resource_type': 'files',
                'resource_id': self.object.id
            }
        )
