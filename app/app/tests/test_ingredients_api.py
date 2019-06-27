from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest

from core.models import Ingredient, Recipe

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

    def test_create_ingredient_successful(self, logged_client, registred_user):
        """Test create a new ingredient"""
        payload = {"name": "Cabbage"}
        response = logged_client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=registred_user,
            name=payload["name"]
        ).exists()

        assert response.status_code == status.HTTP_201_CREATED
        assert exists

    def test_create_ingredient_invalid(self, logged_client, registred_user):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        response = logged_client.post(INGREDIENTS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrive_ingredients_assigned_to_recipes(
        self,
        registred_user,
        logged_client
    ):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(
            user=registred_user, name='Turkey'
        )
        ingredient2 = Ingredient.objects.create(
            user=registred_user, name='Apples'
        )
        recipe = Recipe.objects.create(
            title='Apple crumble',
            time_minutes=5,
            price=10,
            user=registred_user
        )
        recipe.ingredients.add(ingredient2)

        response = logged_client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        assert serializer1.data not in response.data
        assert serializer2.data in response.data

    def test_retrieve_ingredients_assigned_unique(
        self,
        logged_client,
        registred_user
    ):
        """Test filtering ingredienta by assigned return unique items"""
        ingredient = Ingredient.objects.create(
            user=registred_user,
            name='Eggs'
        )
        Ingredient.objects.create(user=registred_user, name='Cheese')
        recipe1 = Recipe.objects.create(
            title='Eggst benedict',
            time_minutes=10,
            price=12.00,
            user=registred_user
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='Coriander eggs',
            time_minutes=20,
            price=6.00,
            user=registred_user
        )
        recipe2.ingredients.add(ingredient)

        response = logged_client.get(INGREDIENTS_URL, {'assigned_only': 1})

        assert len(response.data) == 1
