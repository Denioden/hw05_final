# posts/tests/test_urls.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from posts.models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы',
            slug='slug',
            description='Описание группы'
        )
        # Создаём авторизованного прльзвателя,
        # которой не является автором поста.
        cls.user = User.objects.create_user(username='User')
        # Сздаём автра поста.
        cls.author = User.objects.create_user(username='Author')
        # Создаём пост
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author
        )

    # Создаём пользователя гостя и афторизируем пользователя.
    def setUp(self) -> None:
        cache.clear()
        # Гость
        self.guest_client = Client()
        # Зарегестрированный пользователь - не автор поста)
        self.user_client = Client()
        self.user_client.force_login(self.user)
        # Зарегестрированный пользователь - автор поста)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует ожидаемый шаблон."""
        group = PostURLTests.group
        user = PostURLTests.user
        post = PostURLTests.post

        urls = [
            '/',
            f'/group/{group.slug}/',
            f'/profile/{user}/',
            f'/posts/{post.id}/',
            f'/posts/{post.id}/edit/',
            '/create/',
        ]

        template = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]

        for urls, template in zip(urls, template):
            with self.subTest(urls=urls):
                response = self.author_client.get(urls)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        group = PostURLTests.group
        user = PostURLTests.user
        post = PostURLTests.post

        templates_url_names = [
            '/',
            f'/group/{group.slug}/',
            f'/profile/{user}/',
            f'/posts/{post.id}/'
        ]
        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/<post_id>/edit/ доступна только автору"""
        post = PostURLTests.post
        response = self.author_client.get(f'/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_not_accessible_to_a_non_author(self):
        """"Страница /posts/<post_id>/edit/ не доступна
        пользователю не являюшимся автором"""
        post = PostURLTests.post
        response = self.user_client.get(f'/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_not_available_to_the_guest(self):
        """Страница /posts/<post_id>/edit/ не доступна
        неавторизованному пользователю"""
        post = PostURLTests.post
        response = self.guest_client.get(f'/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.author_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_url_field(self):
        """Вызов не существующего URL-адреса выдаёт ошибку 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
