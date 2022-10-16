import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Follow
from django.conf import settings

from .fixtures.factories import post_create, group_create, url_rev

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
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

    def setUp(self) -> None:
        cache.clear()
        # Создаем гостя
        self.guest_client = Client()
        # Автор(Зарегестрированный пользователь)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_post_edit_url_template_post_and_group(self):
        """Во view-функция используют html-шаблоны сответствующий страницы."""
        cache.clear()
        group = PostURLTests.group
        user = PostURLTests.user
        post = PostURLTests.post

        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=group.slug),
            url_rev('posts:profile', username=user.username),
            url_rev('posts:post_detail', post_id=post.id),
            url_rev('posts:post_edit', post_id=post.id),
            url_rev('posts:post_create'),
        ]

        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]

        for url_name, template in zip(urls, templates):
            with self.subTest(url_name=url_name):
                response = self.author_client.get(url_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_contains_post_and_group(self):
        """Создав пост (см `setUp`), увидим его на страницах:
        index, group_list, profile"""
        group = PostURLTests.group
        post = PostURLTests.post
        image = PostURLTests.image

        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=group.slug),
            url_rev('posts:profile', username=post.author),
        ]

        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get(url_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Текст поста')
                self.assertEqual(post.image, image)

    def test_post_detail_show_contains_post(self):
        """Создав пост (см `setUp`), увидим его на странице /post_detail/"""
        post = PostURLTests.post
        image = PostURLTests.image

        response = self.author_client.get(
            url_rev('posts:post_detail', post_id=post.id)
        )

        post = response.context['post']
        self.assertEqual(post.text, 'Текст поста')
        self.assertEqual(post.image, image)

    def test_post_form_edit_url_contains_post_and_group(self):
        """Шаблоны сформированы с ожидаемым контекстом содержаший form."""
        post = PostURLTests.post

        urls = [
            url_rev('posts:post_create'),
            url_rev('posts:post_edit', post_id=post.id),
        ]

        for url_name in urls:
            response = self.author_client.get(url_name)
            form_fields = {
                'text': forms.CharField,
                'group': forms.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_create_group(self):
        """Создав пост (см `setUp`) с указанием группы,
        он появляется на страницах: index, group_list, profile"""
        group = PostURLTests.group
        post = PostURLTests.post

        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=group.slug),
            url_rev('posts:profile', username=post.author),
        ]
        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get(url_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Текст поста')
                self.assertEqual(post.author.username, 'Author')
                self.assertEqual(post.group.title, 'Название группы')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # Создаём изображение
        cls.image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        # Создаём автора поста
        cls.author = User.objects.create_user('Author')
        # Создаём группу
        cls.group = group_create()

        # Создаём 15 постов
        for i in range(15):
            cls.post = post_create(cls.author, cls.group, cls.image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # Создаём пользователя гостя и афторизируем пользователя.
    def setUp(self) -> None:
        # Автор(Зарегестрированный пользователь)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_first_page_contains_three_records(self):
        """На первой странице: index, group_list,
        profile выводится 10 постов"""
        group = PaginatorViewsTest.group
        post = PaginatorViewsTest.post

        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=group.slug),
            url_rev('posts:profile', username=post.author),
        ]
        for url_name in urls:
            with self.subTest(urls_name=url_name):
                response = self.author_client.get(url_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_first_page_contains_three_records(self):
        """На второй странице: index, group_list,
        profile выводится 5 постов"""
        group = PaginatorViewsTest.group
        post = PaginatorViewsTest.post

        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=group.slug),
            url_rev('posts:profile', username=post.author),
        ]
        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get((url_name) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 5)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CacheTest(TestCase):
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

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_cache_index(self):
        """Список записей главной страници /index/ хранится в кэше"""
        first_state = self.author_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.author_client.get(reverse('posts:index'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(first_state.content, third_state.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        # Создаём пользователя(подписчик)
        cls.follower = User.objects.create_user(username='follower')
        # Создаём автора(на кого подписываемся)
        cls.following = User.objects.create_user(username='following')
        # Создаём группу
        cls.group = group_create()
        # Создаём пост
        cls.post = post_create(cls.following, cls.group, cls.image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        cache.clear()
        self.follower_client = Client()
        self.following_client = Client()

        self.follower_client.force_login(self.follower)
        self.following_client.force_login(self.following)

    def test_follow_index(self):
        """На странице follow пользователь увидит
        посты авторов на которых подписан"""
        follower = FollowTest.follower
        following = FollowTest.following
        Follow.objects.create(user=follower,
                              author=following)
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Текст поста')
        response = self.following_client.get('/follow/')
        self.assertNotContains(response, 'Текст поста')

    def test_follow(self):
        """Пользователь может подписаться на интересного автора"""
        following = FollowTest.following

        self.follower_client.get(
            url_rev('posts:profile_follow', username=following)
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Пользователь может отказаться от подписки
        на неинтерсного автора """
        following = FollowTest.following

        self.follower_client.get(
            url_rev('posts:profile_follow', username=following)
        )
        self.follower_client.get(
            url_rev('posts:profile_unfollow', username=following)
        )
        self.assertEqual(Follow.objects.all().count(), 0)
