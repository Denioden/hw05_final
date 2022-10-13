import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.group = Group.objects.create(
            title='Название группа',
            slug='slug',
            description='Описание'
        )
        cls.user = User.objects.create_user(username='User')
        cls.author = User.objects.create_user(username='Author')
        # Создаём пост
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    # Создаём пользователя гостя и афторизируем пользователя.
    def setUp(self) -> None:
        # Создаем гостя
        self.guest_client = Client()
        # Автор(Зарегестрированный пользователь)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_form_create_new_Post(self):
        """Валидная форма создаёт запись в Post"""
        group = PostCreateFormTests.group
        user = PostCreateFormTests.author

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

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

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Текст поста',
            'group': group.id,
            'image': uploaded.name
        }

        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            url('posts:profile', username=user)
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Изменённый текст поста',
            'group': group.id
        }
        response = self.author_client.post(
            url('posts:post_edit', post_id=post.id),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            url('posts:post_detail', post_id=post.id)
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

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        form_data = {
            'text': 'Коментарий авторизованного пользователя',
        }

        response = self.author_client.post(
            url('posts:add_comment', post_id=post.id),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            url('posts:post_detail', post_id=post.id)
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Коментарий авторизованного пользователя'
            ).exists()
        )

    def test_no_author_comment(self):
        """не авторизованный пользователь не может комментировать;"""
        post = PostCreateFormTests.post

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        form_data = {
            'text': 'Коментарий не авторизованного пользователя',
        }

        self.guest_client.post(
            url('posts:add_comment', post_id=post.id),
            data=form_data,
            follow=True,
        )

        self.assertFalse(
            Comment.objects.filter(
                text='Коментарий не авторизованного пользователя'
            ).exists()
        )
