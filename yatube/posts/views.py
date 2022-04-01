from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from .models import Post, Group, Comment, Follow
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .forms import PostForm, CommentForm
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.decorators import login_required


def index(request):
    # Показывать по 10 записей на странице.
    paginator = Paginator(Post.objects.all(), 10)

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')

    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def group_list(request):
    return render(request, 'posts/group_list.html')


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    user = get_object_or_404(User, username=username)
    paginator = Paginator(Post.objects.filter(author_id=user.id), 10)
    page_number = request.GET.get('page')
    user_posts = paginator.get_page(page_number)
    user_posts_count = user.posts.count()
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(author=user, user=request.user).exists():
            following = True
    context = {
        'page_obj': user_posts,
        'posts_count': user_posts_count,
        'author': user,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, id=post_id)
    user_posts_count = post.author.posts.count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'user_posts_count': user_posts_count,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        text = form.cleaned_data['text']
        group = form.cleaned_data['group']
        author_id = request.user.id
        pub_date = datetime.now()
        files = form.cleaned_data['image']
        Post.objects.create(
            text=text,
            group=group,
            created=pub_date,
            author_id=author_id,
            image=files
        )
        url = reverse(
            'posts:profile',
            kwargs={'username': request.user.username})
        return redirect(url)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author_id != request.user.id:
        url = reverse('posts:post_detail', args={'post_id': post_id})
        return redirect(url)
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        text = form.cleaned_data['text']
        group = form.cleaned_data['group']
        image = form.cleaned_data['image']
        post.text = text
        post.group = group
        post.image = image
        post.save()
        url = reverse('posts:post_detail', kwargs={'post_id': post_id})
        return redirect(url)
    return render(
        request,
        'posts/post_create.html',
        {'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, id=post_id)
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
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if username != request.user.username:
        if not Follow.objects.filter(
            user=request.user,
                author=User.objects.get(username=username)).exists():
            user = request.user
            Follow.objects.create(
                user=user,
                author=author
            )
    return redirect(reverse('posts:follow_index'))


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=user, author=author)
    follow.delete()
    return redirect(reverse('posts:follow_index'))
