import tempfile
import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import pytest

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_basic_recipe(self, logged_client):
        """Test creating recipe"""
        payload = {
            'title': 'Chockolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        response = logged_client.post(RECIPES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload.keys():
            assert payload[key] == getattr(recipe, key)

    def test_create_recipe_with_tags(self, registred_user, logged_client):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=registred_user, name='Vegan')
        tag2 = sample_tag(user=registred_user, name='Dessert')

        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        response = logged_client.post(RECIPES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()
        assert tags.count() == 2
        assert tag1 in tags
        assert tag2 in tags

    def test_create_recipe_with_ingredients(
        self,
        registred_user,
        logged_client
    ):
        """Test creating recipe with ingredients"""
        ingredient1 = sample_ingredient(user=registred_user, name='Prawns')
        ingredient2 = sample_ingredient(user=registred_user, name='Ginger')
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 45,
            'price': 7.00
        }
        response = logged_client.post(RECIPES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()
        assert ingredients.count() == 2
        assert ingredient1 in ingredients
        assert ingredient2 in ingredients

    def test_partial_update_recipe(self, logged_client, registred_user):
        """Test updating recipe with patch"""
        recipe = sample_recipe(user=registred_user)
        recipe.tags.add(sample_tag(user=registred_user))
        new_tag = sample_tag(user=registred_user, name='Curry')

        payload = {'title': 'Chicken tikka', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        logged_client.patch(url, payload)

        recipe.refresh_from_db()
        assert recipe.title == payload['title']

        tags = recipe.tags.all()
        assert len(tags) == 1
        assert new_tag in tags

    def test_full_update_recipe(self, logged_client, registred_user):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=registred_user)
        recipe.tags.add(sample_tag(user=registred_user))
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00
        }
        url = detail_url(recipe.id)
        logged_client.put(url, payload)

        recipe.refresh_from_db()
        assert recipe.title == payload['title']
        assert recipe.time_minutes == payload['time_minutes']
        assert recipe.price == payload['price']

        tags = recipe.tags.all()
        assert len(tags) == 0


@pytest.mark.django_db
class TestRecipeImageUpload():
    def test_upload_image_to_recipe(self, logged_client, registred_user):
        """Test uploading an email to recipe"""
        recipe = sample_recipe(user=registred_user)
        url = image_upload_url(recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            response = logged_client.post(
                url,
                {'image': ntf},
                format="multipart"
            )
        recipe.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert 'image' in response.data
        assert os.path.exists(recipe.image.path)

    def test_upload_image_bad_request(self, logged_client, registred_user):
        """Test uploading a invalid image"""
        recipe = sample_recipe(user=registred_user)
        url = image_upload_url(recipe.id)
        response = logged_client.post(
            url,
            {'image': 'img'},
            format='multipart'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_recipes_by_tags(self, logged_client, registred_user):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=registred_user, title='Thai vege curry')
        recipe2 = sample_recipe(
            user=registred_user,
            title='Aubergine with tahini'
        )
        tag1 = sample_tag(user=registred_user, name='Vegan')
        tag2 = sample_tag(user=registred_user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=registred_user, title='Fish and chips')

        response = logged_client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id}, {tag2.id}'}
        )
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        assert len(response.data) == 2
        assert serializer1.data in response.data
        assert serializer2.data in response.data
        assert serializer3.data not in response.data

    def test_filter_recipes_by_ingredients(
        self,
        logged_client,
        registred_user
    ):
        """Test returning recipes with specific ingredients"""
        recipe1 = sample_recipe(user=registred_user, title='Beans tost')
        recipe2 = sample_recipe(user=registred_user, title='Chicken')
        ingredient1 = sample_ingredient(user=registred_user, name='beans')
        ingredient2 = sample_ingredient(user=registred_user, name='soy')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=registred_user, title='mushrooms')

        response = logged_client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        assert len(response.data) == 2
        assert serializer1.data in response.data
        assert serializer2.data in response.data
        assert serializer3.data not in response.data
