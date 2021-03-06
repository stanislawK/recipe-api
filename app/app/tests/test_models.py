import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from core import models


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

    def test_tag_str(self, registred_user):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=registred_user,
            name='Vegan'
        )

        assert str(tag) == tag.name

    def test_ingredient_str(self, registred_user):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=registred_user,
            name='Cucumber'
        )

        assert str(ingredient) == ingredient.name

    def test_recipe_str(self, registred_user):
        """Test the recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=registred_user,
            title='Vege pasta',
            time_minutes=5,
            price=5.00
        )

        assert str(recipe) == recipe.title

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe/{uuid}.jpg'

        assert file_path == exp_path
