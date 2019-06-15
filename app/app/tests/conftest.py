import os
import django
from django.conf import settings
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
