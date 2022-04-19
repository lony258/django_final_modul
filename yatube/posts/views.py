from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment

COUNT_PAGE = 10


def paginator(request, posts):
    paginator = Paginator(posts, COUNT_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    posts = Post.objects.all()
    page_obj = paginator(request, posts)

    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = (
        Post.objects
        .filter(group=group)
    )
    page_obj = paginator(request, posts)

    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author.pk)
    post_numbers = Post.objects.filter(author=author.pk).count()
    page_obj = paginator(request, posts)

    context = {
        'author': author,
        'posts_numbers': post_numbers,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_numbers = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        return redirect('posts: add_comment')
    context = {
        'post': post,
        'posts_numbers': post_numbers,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=post.author)

        return render(request, 'posts/create_post.html', {'form': form})

    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
