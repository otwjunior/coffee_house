from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User


class UserAuthTests(TestCase):
    """Tests for user authentication endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')        # ← Fixed: was wrong/missing
        self.me_url = reverse('users:me')
        self.profile_url = reverse('users:profile')    # ← Fixed quote typo
        self.logout_url = reverse('users:logout')      # ← Fixed wrong namespace

    def test_customer_registration_success(self):
        """Normal customer can register successfully"""
        payload = {
            "email": "mocha@coffeehouse.com",
            "full_name": "Mocha Lover",
            "password": "supersecret123",
            "password2": "supersecret123"
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="mocha@coffeehouse.com").exists())  # ← fixed .exist()

        user = User.objects.get(email="mocha@coffeehouse.com")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("supersecret123"))

    def test_customer_registration_password_mismatch(self):
        """Registration fails when passwords don't match"""
        payload = {
            "email": "latte@coffeehouse.com",
            "full_name": "Latte Fan",
            "password": "pass123",
            "password2": "pass124"
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="latte@coffeehouse.com").exists())  # ← fixed asserFalse

    def test_customer_can_login(self):
        """Registered customer can obtain JWT tokens"""
        # Register first
        user_data = {
            "email": "espresso@coffeehouse.com",
            "full_name": "Espresso Shot",
            "password": "mypass123",
            "password2": "mypass123"
        }
        self.client.post(self.register_url, user_data, format='json')

        # Now login
        login_payload = {
            "email": "espresso@coffeehouse.com",
            "password": "mypass123"
        }
        login_response = self.client.post(self.login_url, login_payload, format='json')  # ← Fixed: was self.token_url

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)  # ← fixed asserEqual
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)

    def test_staff_creation_requires_special_flow(self):
        """Regular registration should never create staff user"""
        response = self.client.post(self.register_url, {
            "email": "barista@coffeehouse.com",
            "full_name": "Barista Joe",
            "password": "barista123",
            "password2": "barista123"
        }, format='json')  # ← missing comma fixed

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="barista@coffeehouse.com")  # ← fixed user.User.objects.get
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_staff_cannot_be_created_via_public_register(self):
        """Even if malicious payload sends is_staff=True, it must be ignored"""
        malicious_payload = {
            "email": "hacker@coffeehouse.com",
            "full_name": "Bad Actor",
            "password": "hack123",
            "password2": "hack123",
            "is_staff": True,
            "is_superuser": True
        }
        response = self.client.post(self.register_url, malicious_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # ← fixed reponse → response

        user = User.objects.get(email="hacker@coffeehouse.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)