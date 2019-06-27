from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class TestPublicTagsApi():
    """Test rhe publicly available tags API"""

    def setup_method(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retriving tags"""
        response = self.client.get(TAGS_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateTagsApi():
    """Test the authorized user tags API"""

    def test_retrive_empty(self, logged_client):
        """Test retrive emty tag list"""
        response = logged_client.get(TAGS_URL)
        assert len(response.data) == 0

    def test_retrive_tags(self, registred_user, logged_client):
        """Test retriving tags"""
        Tag.objects.create(user=registred_user, name='Vegan')
        Tag.objects.create(user=registred_user, name='Dessert')

        response = logged_client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_tags_limited_to_user(self, registred_user, logged_client):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'test2@test.com',
            'pass1234'
        )
        Tag.objects.create(user=user2, name="Fruity")
        Tag.objects.create(user=registred_user, name='Thai')

        response = logged_client.get(TAGS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Thai'

    def test_create_tag_succesful(self, logged_client, registred_user):
        """Tast creating a new tag"""
        payload = {'name': 'Test tag'}
        response = logged_client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=registred_user,
            name=payload['name']
        ).exists()

        assert response.status_code == status.HTTP_201_CREATED
        assert exists

    def test_create_tag_invalid(self, logged_client):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        response = logged_client.post(TAGS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrive_tags_assigned_to_recipes(
        self,
        registred_user,
        logged_client
    ):
        """Test filtering tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=registred_user, name='Breakfast')
        tag2 = Tag.objects.create(user=registred_user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5,
            user=registred_user
        )
        recipe.tags.add(tag1)

        response = logged_client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        assert serializer1.data in response.data
        assert serializer2.data not in response.data

    def test_retrive_tags_assigned_unique(self, registred_user, logged_client):
        """Test filtering tags by assigned returns unique items"""
        tag1 = Tag.objects.create(user=registred_user, name='Breakfast')
        Tag.objects.create(user=registred_user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=10,
            price=7.00,
            user=registred_user
        )
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user=registred_user
        )
        recipe2.tags.add(tag1)

        response = logged_client.get(TAGS_URL, {'assigned_only': 1})

        assert len(response.data) == 1
