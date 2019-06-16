import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


@pytest.mark.django_db
class TestPublicUser:
    """Test the users API public"""

    def setup_method(self):
        self.client = APIClient()

    def test_create_valid_user_success(self, new_user):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': new_user['email'],
            'password': new_user['password'],
            'name': new_user['email']
        }

        response = self.client.post(USER_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(**response.data)
        assert user.check_password(payload['password'])
        assert payload['password'] not in response.data

    def test_user_exists(self, new_user, registred_user):
        """Test creating user that already exist fails"""
        payload = {
            'email': new_user['email'],
            'password': new_user['password']
        }
        response = self.client.post(USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_too_short(self, new_user):
        """Test that the password must be more then 5 characters"""
        payload = {
            'email': new_user['email'],
            'password': 'pw'
        }

        response = self.client.post(USER_URL, params=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_for_user(self, new_user, registred_user):
        """Test that token is created for the user"""
        payload = {
            'email': new_user['email'],
            'password': new_user['password']
        }
        response = self.client.post(TOKEN_URL, payload)

        assert 'token' in response.data
        assert response.status_code == status.HTTP_200_OK

    def test_create_token_invalid_credentials(self, new_user, registred_user):
        """Test that token is not created if invalid credentails are given"""
        payload = {'email': new_user['email'], 'password': 'wrongpass'}
        response = self.client.post(TOKEN_URL, payload)

        assert 'token' not in response.data
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_no_user(self, new_user):
        """Test that token is not created if user doesn't exist"""
        payload = {
            'email': new_user['email'],
            'password': new_user['password']
        }
        response = self.client.post(TOKEN_URL, payload)

        assert 'token' not in response.data
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_missing_field(self, new_user):
        """Test that email and password are required"""
        payload = {
            'email': new_user['email'],
            'password': ''
        }
        response = self.client.post(TOKEN_URL, payload)

        assert 'token' not in response.data
        assert response.status_code == status.HTTP_400_BAD_REQUEST
