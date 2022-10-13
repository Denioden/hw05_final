# views Отвечает за представление сайта
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .utils import create_paginator

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


# Главная страница
@cache_page(20)
def index(request):
    # выводит все объекты  класса POST из models
    posts = Post.objects.all()
    page_obj = create_paginator(posts, request.GET.get('page'))
    # _obj обозначает что переменная содержит объект paginator
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'posts': posts,
        'page_obj': page_obj,
    }

    template = 'posts/index.html'
    return render(request, template, context)


# группа с постами
def group_posts(request, slug):
    # slug-название группы переданное в URL
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    page_obj = create_paginator(posts, request.GET.get('page'))

    title = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }

    template = 'posts/group_list.html'
    return render(request, template, context)


# Страница профайла пользователя: на ней будет отображаться
# информация об авторе и его посты
def profile(request, username):
    user = get_object_or_404(User, username=username)
    author_posts = Post.objects.filter(author=user)
    page_obj = create_paginator(author_posts, request.GET.get('page'))
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user
        ).exists()
    else:
        following = False
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }

    template = 'posts/profile.html'
    return render(request, template, context)


# Страница для просмотра отдельного поста
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comment,
        'form': form
    }

    template = 'posts/post_detail.html'
    return render(request, template, context)


# Новая запись
@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():  # form.is_valid проверка коректности данных
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    else:
        form = PostForm()

    context = {
        'form': form,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:profile', request.user.username)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():  # form.is_valid проверка коректности данных
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', str(post_id))

    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    list_post = Post.objects.filter(author__following__user=request.user)
    page_obj = create_paginator(list_post, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/follow.html'
    return render(request, template, context)


# Функция для подписки на автора поста
@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(user=user, author=author)
    if user != author and not is_following.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=author)


# Функция для отписки от автора поста.
@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
