import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestModels:

    def test_create_user_with_email_successful(self, new_user):
        """Test creating a new user with an email is successful"""
        user = get_user_model().objects.create_user(
            email=new_user["email"],
            password=new_user["password"]
        )

        assert user.email == new_user["email"]
        assert user.check_password(new_user["password"])

    def test_new_user_email_normalized(self, new_user):
        """Test the email for a new user is normalized"""
        email = new_user['email'].split('@')
        email = '@'.join([email[0], email[1].upper()])
        user = get_user_model().objects.create_user(
            email=email,
            password=new_user['password']
        )

        assert len(get_user_model().objects.all()) > 0
        assert user.email == new_user['email']

    def test_new_user_invalid_email(self, new_user):
        """Test creating user with no email raises error"""
        with pytest.raises(ValueError) as error:
            get_user_model().objects.create_user(
                email=None,
                password=new_user['password']
            )

            assert error == 'User must have an email adress'

    def test_create_new_superuser(self, new_user):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            new_user['email'],
            new_user['password']
        )

        assert user.is_superuser
        assert user.is_staff
