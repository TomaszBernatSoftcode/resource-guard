import os

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from dropbox import dropbox


class SecuredResource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource_route = models.CharField(unique=True, max_length=128)
    password = models.CharField(max_length=96)
    creation_date = models.DateField()
    expire_ts = models.DateTimeField()
    visit_counter = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    latest_user_agent = models.CharField(null=False, blank=True, max_length=64)

    class Meta:
        abstract = True

    def is_accessible(self):
        return self.expire_ts > timezone.now()


class SecuredUrl(SecuredResource):
    url_route = models.URLField(max_length=2048)

    def __str__(self):
        return "{user} - {urlroute}".format(user=self.user.username, urlroute=self.url_route)


def upload_to(instance, filename):
    upload_path = '{}/{}'.format(
        instance.user.username, filename
    )
    if settings.DEBUG:
        return 'media/{}'.format(upload_path)
    return upload_path


class SecuredFile(SecuredResource):
    file_size = models.PositiveIntegerField()
    persisted_file = models.FileField(upload_to=upload_to)

    def __str__(self):
        return "{user} - {filename}".format(user=self.user.username, filename=self.persisted_file.name)

    def save(self, *args, **kwargs):
        self.file_size = self.persisted_file.size
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=SecuredFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.persisted_file:
        dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        dbx.files_delete_v2("{}{}".format(settings.DROPBOX_ROOT_PATH, instance.persisted_file.name))


@receiver(models.signals.pre_save, sender=SecuredFile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = SecuredFile.objects.get(pk=instance.pk).persisted_file
    except SecuredFile.DoesNotExist:
        return False

    new_file = instance.persisted_file
    if not old_file == new_file:
        dbx = dropbox.Dropbox(settings.DROPBOX_OAUTH2_TOKEN)
        dbx.files_delete_v2("{}{}".format(settings.DROPBOX_ROOT_PATH, instance.persisted_file.name))
