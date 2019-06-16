import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
class TestAdmin:

    def test_registred_user(self, registred_user):
        user = get_user_model().objects.all()[0]
        assert user.email == "test@test.com"

    def test_user_listed(self, client, admin_user, registred_user):
        """Test that users are listed on user page"""
        url = reverse('admin:core_user_changelist')
        client.force_login(admin_user)
        res = client.get(url)

        assert res.status_code == 200
        assert registred_user.email in str(res.content)

    def test_user_cahnge_page(self, client, admin_user, registred_user):
        """Test that the user edid page works"""
        url = reverse('admin:core_user_change', args=[registred_user.id])
        client.force_login(admin_user)
        res = client.get(url)

        assert res.status_code == 200

    def test_create_user_page(self, client, admin_user):
        """Test that the create user page works"""
        url = reverse('admin:core_user_add')
        client.force_login(admin_user)
        res = client.get(url)

        assert res.status_code == 200
