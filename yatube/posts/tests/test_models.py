from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user('Author')
        cls.group = Group.objects.create(
            title='Название группы',
            slug='slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Максимум 15 символов',
        )

    def test_models_have_correct_object_names_post(self):
        """Значение поля __str__ в объекте
        модели Post совподает с ожидаемым."""
        post = PostModelTest.post
        expected_object_name = 'Максимум 15 символов'[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_models_have_correct_object_names_group(self):
        """Значение поля __str__ в объекте
        модели Group совподает с ожидаемым."""
        group = PostModelTest.group
        self.assertEqual('Название группы', str(group))
