from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class LoginFlowTests(TestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_redirects_authenticated_user(self):
        user = get_user_model().objects.create_user(username='existing', password='StrongPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get('Location'), '/dashboard/')

    def test_settings_requires_login(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.headers.get('Location', ''))

    def test_user_can_register_and_login(self):
        register_response = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'email': 'newuser@example.com', 'password1': 'StrongPass123', 'password2': 'StrongPass123'},
            follow=True,
        )
        self.assertEqual(register_response.status_code, 200)

        user = get_user_model().objects.get(username='newuser')
        self.assertTrue(user.is_authenticated)

        login_response = self.client.post(
            reverse('login'),
            {'username': 'newuser', 'password': 'StrongPass123'},
            follow=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'Welcome')
