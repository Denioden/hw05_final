from django.urls import reverse
from posts.models import Post, Group


def url_rev(url, **kwargs):
    return reverse(url, kwargs=kwargs)


def post_create(user, group, image):
    return Post.objects.create(
        text='Текст поста',
        author=user,
        group=group,
        image=image
    )


def group_create():
    return Group.objects.create(
        title='Название группы',
        slug='slug',
        description='Описание группы',
    )
