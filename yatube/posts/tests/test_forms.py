from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class PostFormTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user
        )

    def test_create_post(self):
        """Валидная форма создает запись в Task."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={
                    'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            Post.objects.get(
                pk=self.post.pk).text, 'Тестовый заголовок')

    def test_post_edit(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст измененный',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            Post.objects.get(
                pk=self.post.pk).text,
            'Тестовый текст измененный')
