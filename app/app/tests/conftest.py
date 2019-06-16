import os
import django
from django.conf import settings
from django.contrib.auth import get_user_model
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')


def pytest_configure():
    settings.DEBUG = False
    django.setup()


@pytest.fixture
def new_user():
    user = {
        "email": "test@test.com",
        "password": "pass123",
    }
    return user


@pytest.fixture
@pytest.mark.django_db
def registred_user(new_user):
    user = get_user_model().objects.create_user(
        email=new_user["email"],
        password=new_user["password"]
    )
    return user


@pytest.fixture
@pytest.mark.django_db
def admin_user(new_user):
    user = get_user_model().objects.create_superuser(
        email="admin@test.com",
        password=new_user["password"]
    )
    return user
