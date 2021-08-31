from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm

from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    """View - функция для главной страницы проекта."""

    posts = Post.objects.all()
    paginator = Paginator(posts, settings.PAGINATOR)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View - функция для страницы с постами, отфильтрованными по группам."""

    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, settings.PAGINATOR)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,

    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """View - функция для страницы с постами пользователя,
       вошедшего на сайт.
    """

    author = get_object_or_404(User, username=username)

    count = author.posts.all().count()
    paginator = Paginator(author.posts.all(), settings.PAGINATOR)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )

    context = {'author': author,
               'count': count,
               'page_obj': page_obj,
               'following': following,

               }
    return render(request, 'posts/profile.html', context)


def post_view(request, post_id):
    """View - функция для страницы определенного поста."""

    post = get_object_or_404(Post, pk=post_id)
    count = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    comment = Comment.objects.filter(post=post.pk)

    context = {'post': post,
               'count': count,
               'form': form,
               'comment': comment,
               }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """View - функция для создания поста."""

    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/create_post.html', {"form": form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {"form": form, })


@login_required
def post_edit(request, post_id):
    """View - функция для редактирования проекта."""

    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail',
                        files=request.FILES or None,
                        pk=post_id)
    else:
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html',
                  {"form": form, 'post': post, "is_edit": is_edit, })


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
    """View - функция для главной страницы подписок."""

    posts = Post.objects.filter(author__following__user=request.user).all()
    paginator = Paginator(posts, settings.PAGINATOR)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    if request.user.username == username:
        return redirect('posts:profile', username=username)
    author_follow = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(
        user=request.user,
        author=author_follow
    ).exists()
    if not follows:
        Follow.objects.create(user=request.user, author=author_follow)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""

    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(author=author,
                                user=request.user)
    if Follow.objects.filter(pk=follow.pk).exists():
        follow.delete()
    return redirect('posts:profile', username=username)
