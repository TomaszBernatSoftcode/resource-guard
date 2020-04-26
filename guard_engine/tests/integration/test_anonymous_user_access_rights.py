import datetime
import mock

from uuid import uuid4

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.utils import timezone
from django.core.files import File

from guard_engine.models import SecuredUrl, SecuredFile
from guard_engine.views import resource_verifier, user_resources, SecuredUrlCreate, SecuredFileCreate


class AnonymousUserAccessTestCase(TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.anonymous_user = AnonymousUser()

    def test_anonymous_user_has_no_access_to_main_site(self):
        request = self.factory.get('')
        request.user = self.anonymous_user
        response = user_resources(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login?next=/')

    def test_anonymous_user_has_no_access_to_resource_creation_form(self):
        secure_url_request = self.factory.get('/secure-url')
        secure_url_request.user = self.anonymous_user
        secure_url_response = SecuredUrlCreate.as_view()(secure_url_request)

        self.assertEqual(secure_url_response.status_code, 302)
        self.assertEqual(secure_url_response.url, '/login?next=/secure-url')

        secure_file_request = self.factory.get('/secure-file')
        secure_file_request.user = self.anonymous_user
        secure_url_response = SecuredFileCreate.as_view()(secure_file_request)

        self.assertEqual(secure_url_response.status_code, 302)
        self.assertEqual(secure_url_response.url, '/login?next=/secure-file')

    def test_anonymous_user_has_no_access_to_secured_resource(self):
        logged_in_user = User.objects.create_user(username='johnDoe', email='john@doe.com', password='testPassword123')

        url_creation_ts = timezone.now()
        url_resource_uid = uuid4().time_low
        secured_url = SecuredUrl(
            user=logged_in_user,
            resource_route="{user_name}/urls/{resource_uid}".format(
                user_name=logged_in_user.username,
                resource_uid=url_resource_uid
            ),
            password="verySecretPasswordUrl",
            creation_date=url_creation_ts.date(),
            expire_ts=url_creation_ts + datetime.timedelta(days=1),
            latest_user_agent='Mozilla/5.0',
            url_route='https://www.google.pl/'
        )

        secured_url_route = '/' + secured_url.resource_route
        secured_url_request = self.factory.get(secured_url_route)
        secured_url_request.user = self.anonymous_user
        secured_url_response = resource_verifier(secured_url_request)

        self.assertEqual(secured_url_response.status_code, 302)
        self.assertEqual(secured_url_response.url, '/login?next=' + secured_url_route)

        file_creation_ts = timezone.now()
        file_resource_uid = uuid4().time_low
        mocked_file = mock.MagicMock(spec=File)
        mocked_file.name = 'test.pdf'
        secured_file = SecuredFile(
            user=logged_in_user,
            resource_route="{user_name}/urls/{resource_uid}".format(
                user_name=logged_in_user.username,
                resource_uid=file_resource_uid
            ),
            password="verySecretPasswordFile",
            creation_date=file_creation_ts.date(),
            expire_ts=file_creation_ts + datetime.timedelta(days=1),
            latest_user_agent='Mozilla/5.0',
            persisted_file=mocked_file
        )

        secured_file_route = '/' + secured_file.resource_route
        secured_file_request = self.factory.get(secured_file_route)
        secured_file_request.user = self.anonymous_user
        secured_file_response = resource_verifier(secured_file_request)

        self.assertEqual(secured_file_response.status_code, 302)
        self.assertEqual(secured_file_response.url, '/login?next=' + secured_file_route)
