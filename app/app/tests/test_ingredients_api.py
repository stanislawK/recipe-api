from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class TestPulicIngredientApi():
    """Test the private ingredients API"""

    def test_login_required(self):
        response = APIClient().get(INGREDIENTS_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateIngredientsApi():
    """Test ingredients can be retrieved by authorized user"""

    def test_retrive_ingredient_list(self, logged_client, registred_user):
        """Test retrieving a list og ingredients"""
        Ingredient.objects.create(user=registred_user, name="Kale")
        Ingredient.objects.create(user=registred_user, name="Salt")

        response = logged_client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_ingredients_limited_to_user(self, logged_client, registred_user):
        """Test that ingredients for authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            'user2@test.com',
            'pass123'
        )
        Ingredient.objects.create(user=user2, name='Vineger')
        ingredient = Ingredient.objects.create(
            user=registred_user,
            name="Kale"
        )
        response = logged_client.get(INGREDIENTS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == ingredient.name
