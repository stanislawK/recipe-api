from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import pytest

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinamon'):
    return Ingredient.objects.create(user=user, name=name)


class TestPublicRecipeApi():
    """Test unauthenticated recipe API access"""

    def test_auth_required(self):
        """Test that authentication is required"""
        response = APIClient().get(RECIPES_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateRecipeApi():
    """Test unauthenticated recipe API access"""

    def test_retrive_recipes(
        self,
        logged_client,
        registred_user
    ):
        """Test retieving a list of recipes"""
        sample_recipe(user=registred_user)
        sample_recipe(user=registred_user)

        response = logged_client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_recipes_limited_to_user(
        self,
        logged_client,
        registred_user,
    ):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            'test2@admin.com',
            'pass123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=registred_user)

        response = logged_client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=registred_user)
        serializer = RecipeSerializer(recipes, many=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data == serializer.data

    def test_view_recipe_detail(sefl, logged_client, registred_user):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=registred_user)
        recipe.tags.add(sample_tag(user=registred_user))
        recipe.ingredients.add(sample_ingredient(user=registred_user))

        url = detail_url(recipe.id)
        response = logged_client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        assert response.data == serializer.data
