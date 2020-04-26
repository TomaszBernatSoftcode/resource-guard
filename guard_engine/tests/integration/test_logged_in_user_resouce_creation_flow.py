from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User

from guard_engine.views import user_resources


class LoggedInUserAccessTestCase(TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.created_user = User.objects.create_user(username='johnDoe', email='john@doe.com', password='testPassword123')

        self.client.login(username='johnDoe', password='testPassword123')

    def tearDown(self):
        self.created_user.delete()

    def test_logged_in_user_can_access_main_site(self):
        request = self.factory.get('')
        request.user = self.created_user
        response = user_resources(request)

        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_can_secure_link(self):
        secure_url_response = self.client.post(
            '/secure-url',
            data={'url_route': 'https://www.google.pl/'},
            **{'HTTP_USER_AGENT': 'Mozilla/5.0'}
        )

        self.assertEqual(secure_url_response.status_code, 302)
        self.assertEqual(secure_url_response.url, '/urls/1/details')

        secured_url_details_response = self.client.get(secure_url_response.url)
        response_context = secured_url_details_response.context

        self.assertEqual(secured_url_details_response.status_code, 200)
        self.assertIsNotNone(response_context['password'])
        self.assertIsNotNone(response_context['resource_route'])
        self.assertIsNotNone(response_context['expire_ts'])

    def test_logged_in_user_can_secure_file(self):
        with open('../test_files/test_file.txt') as test_file:
            secure_file_response = self.client.post(
                '/secure-file',
                data={'persisted_file': test_file},
                **{'HTTP_USER_AGENT': 'Mozilla/5.0'}
            )
            test_file.close()

        self.assertEqual(secure_file_response.status_code, 302)
        self.assertEqual(secure_file_response.url, '/files/1/details')

        secured_file_details_response = self.client.get(secure_file_response.url)
        response_context = secured_file_details_response.context

        self.assertEqual(secured_file_details_response.status_code, 200)
        self.assertIsNotNone(response_context['password'])
        self.assertIsNotNone(response_context['resource_route'])
        self.assertIsNotNone(response_context['expire_ts'])

