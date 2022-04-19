from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is test description'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.user_no_author = User.objects.create_user(username='HasNoAuthor')
        self.authorized_client = Client()
        self.authorized_client_no_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author.force_login(self.user_no_author)

        Post.objects.create(
            text='Test post text',
            group=Group.objects.get(pk=1),
            author=self.user
        )
        self.post_pk = Post.objects.get(pk=1).pk
        self.post_slug = Group.objects.get(pk=1).slug

    def test_urls_404(self):
        """Несуществующая страница /posts/lost/ возвращает 404."""
        response = self.authorized_client.get('/posts/lost/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post_slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post_pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post_pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_guest_client(self):
        """Страницы доступны любому пользователю."""
        url_names = (
            '/',
            f'/group/{self.post_slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post_pk}/',
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_exists_at_desired_location_authorized_client(self):
        """Страницы доступны авторизованному пользователю."""
        url_names = (
            '/',
            f'/group/{self.post_slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post_pk}/',
            '/create/',
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_exists_at_desired_location_author(self):
        """Страница /posts/1/edit/ доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post_pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_exists_at_desired_location_not_author(self):
        """Страница /posts/1/edit/ редиректит, если пользак не автор."""
        response = (
            self.authorized_client_no_author.
            get(f'/posts/{self.post_pk}/edit/')
        )
        self.assertRedirects(response, f'/posts/{self.post_pk}/')

    def test_redirect_url(self):
        """Страницы /create/ и /posts/1/edit/ редиректят, если пользак не
        авторизован."""
        redirect_names = {
            '/create/':
            '/auth/login/?next=/create/',
            f'/posts/{self.post_pk}/edit/':
            f'/auth/login/?next=/posts/{self.post_pk}/edit/'
        }
        for address, redirect_address in redirect_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertRedirects(response, redirect_address)
