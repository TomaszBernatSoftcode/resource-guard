import datetime

from uuid import uuid4

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from guard_engine.models import SecuredUrl, SecuredFile


class ResourcesTestCase(TestCase):

    def setUp(self) -> None:
        self.created_user = User.objects.create_user(username='johnDoe', email='john@doe.com', password='testPassword123')
        self.client.login(username='johnDoe', password='testPassword123')

        url_creation_ts = timezone.now()
        url_resource_uid = uuid4().time_low
        self.secured_url = SecuredUrl.objects.create(
            user=self.created_user,
            resource_route="{user_name}/urls/{resource_uid}".format(
                user_name=self.created_user.username,
                resource_uid=url_resource_uid
            ),
            password="verySecretPasswordUrl",
            creation_date=url_creation_ts.date(),
            expire_ts=url_creation_ts + datetime.timedelta(days=1),
            latest_user_agent='Mozilla/5.0',
            url_route='https://www.google.pl/'
        )

        with open('../test_files/test_file.txt') as test_file:
            self.client.post(
                '/secure-file',
                data={'persisted_file': test_file},
                **{'HTTP_USER_AGENT': 'Mozilla/5.0'}
            )
            test_file.close()

        self.secured_file = SecuredFile.objects.first()

    def tearDown(self):
        self.created_user.delete()
        self.secured_url.delete()
        self.secured_file.delete()

    def test_secured_link_access_available(self):
        secured_url_response = self.client.get('/' + self.secured_url.resource_route)

        self.assertEqual(secured_url_response.status_code, 200)

    def test_secured_link_access_expired(self):
        self.secured_url.expire_ts -= datetime.timedelta(days=1, minutes=30)
        self.secured_url.save()
        secured_url_response = self.client.get('/' + self.secured_url.resource_route)

        self.assertEqual(secured_url_response.status_code, 404)

    def test_secured_file_access_available(self):
        secured_file_response = self.client.get('/' + self.secured_file.resource_route)

        self.assertEqual(secured_file_response.status_code, 200)
        try:
            with open('../../../media/johnDoe/test_file.txt') as test_file:
                self.assertTrue(True)
        except FileNotFoundError:
            self.assertTrue(False, msg="Created file hasn't been saved")

    def test_secured_file_access_expired(self):
        self.secured_file.expire_ts -= datetime.timedelta(days=1, minutes=30)
        self.secured_file.save()
        secured_file_response = self.client.get('/' + self.secured_file.resource_route)

        self.assertEqual(secured_file_response.status_code, 404)
        try:
            with open('../../../media/johnDoe/test_file.txt') as test_file:
                self.assertTrue(False, msg="Deleted file still exists")
        except FileNotFoundError:
            self.assertTrue(True)
