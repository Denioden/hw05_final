import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, Follow
from django.conf import settings

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='gif',
            content=gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Название группы',
            slug='slug',
            description='Описание группы',
        )
        cls.user = User.objects.create_user(username='User')
        # Создаём автора поста
        cls.author = User.objects.create_user(username='Author')
        # Создаём пост
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=group.slug),
            url('posts:profile', username=user.username),
            url('posts:post_detail', post_id=post.id),
            url('posts:post_edit', post_id=post.id),
            url('posts:post_create'),
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=group.slug),
            url('posts:profile', username=post.author),
        ]

        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get(url_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Текст поста')
                self.assertEqual(post.image, 'posts/gif')

    def test_post_detail_show_contains_post(self):
        """Создав пост (см `setUp`), увидим его на странице /post_detail/"""
        post = PostURLTests.post

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        response = self.author_client.get(
            url('posts:post_detail', post_id=post.id)
        )

        post = response.context['post']
        self.assertEqual(post.text, 'Текст поста')
        self.assertEqual(post.image, 'posts/gif')

    def test_post_form_edit_url_contains_post_and_group(self):
        """Шаблоны сформированы с ожидаемым контекстом содержаший form."""
        post = PostURLTests.post

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:post_create'),
            url('posts:post_edit', post_id=post.id),
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=group.slug),
            url('posts:profile', username=post.author),
        ]
        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get(url_name)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Текст поста')
                self.assertEqual(post.author.username, 'Author')
                self.assertEqual(post.group.title, 'Название группы')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы',
            slug='slug',
            description='Описание группы'
        )
        # Создаём автора поста
        cls.author = User.objects.create_user(username='Author')
        # Создаём 15 постов
        for i in range(15):
            cls.post = Post.objects.create(
                text=f'Текст поста{i}',
                author=cls.author,
                group=cls.group,
            )

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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=group.slug),
            url('posts:profile', username=post.author),
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=group.slug),
            url('posts:profile', username=post.author),
        ]
        for url_name in urls:
            with self.subTest(url_name=url_name):
                response = self.author_client.get((url_name) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 5)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        # Создаём автора поста
        cls.author = User.objects.create_user(username='Author')
        # Создаём пост
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
        )

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
        image = tempfile.NamedTemporaryFile(suffix=".jpg").name

        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')

        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.following,
            image=image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        cache.clear()
        # Подписчик(активный пользователь)
        self.follower_client = Client()
        # автор (На кого подписываемся)
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)
        self.follower_client.get(
            url('posts:profile_follow', username=following)
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Пользователь может отказаться от подписки
        на неинтерсного автора """
        following = FollowTest.following

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)
        self.follower_client.get(
            url('posts:profile_follow', username=following)
        )
        self.follower_client.get(
            url('posts:profile_unfollow', username=following)
        )
        self.assertEqual(Follow.objects.all().count(), 0)
