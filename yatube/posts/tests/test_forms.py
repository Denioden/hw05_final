import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .fixtures.factories import post_create, group_create, url_rev

from posts.models import Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаём изображение
        cls.image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        # Создаём пользователя
        cls.user = User.objects.create_user('User')
        # Создаём автора поста
        cls.author = User.objects.create_user('Author')
        # Создаём группу
        cls.group = group_create()
        # Создаём пост
        cls.post = post_create(cls.author, cls.group, cls.image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # Создаём пользователя гостя и афторизируем пользователя.
    def setUp(self) -> None:
        # Создаем гостя
        self.guest_client = Client()
        # Автор(Зарегестрированный пользователь)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_form_create_new_Post(self):
        """Валидная форма создаёт запись в Post"""
        group = PostCreateFormTests.group
        user = PostCreateFormTests.author
        image = PostCreateFormTests.image

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Текст поста',
            'group': group.id,
            'image': image
        }

        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            url_rev('posts:profile', username=user)
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                group=group
            ).exists()
        )

    def test_form_create_change_Post(self):
        """"Изменение существующего поста в базе данных."""
        group = PostCreateFormTests.group
        post = PostCreateFormTests.post

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Изменённый текст поста',
            'group': group.id
        }
        response = self.author_client.post(
            url_rev('posts:post_edit', post_id=post.id),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            url_rev('posts:post_detail', post_id=post.id)
        )

        self.assertEqual(Post.objects.count(), posts_count)

        first_post = Post.objects.first()

        self.assertEqual(
            first_post.text,
            'Изменённый текст поста'
        )

    def test_author_comment(self):
        """комментировать посты может только авторизованный пользователь;"""
        post = PostCreateFormTests.post

        form_data = {
            'text': 'Коментарий авторизованного пользователя',
        }

        response = self.author_client.post(
            url_rev('posts:add_comment', post_id=post.id),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            url_rev('posts:post_detail', post_id=post.id)
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Коментарий авторизованного пользователя'
            ).exists()
        )

    def test_no_author_comment(self):
        """не авторизованный пользователь не может комментировать;"""
        post = PostCreateFormTests.post

        form_data = {
            'text': 'Коментарий не авторизованного пользователя',
        }

        self.guest_client.post(
            url_rev('posts:add_comment', post_id=post.id),
            data=form_data,
            follow=True,
        )

        self.assertFalse(
            Comment.objects.filter(
                text='Коментарий не авторизованного пользователя'
            ).exists()
        )
