import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post
from posts.views import COUNT_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PaginatorViewsTest(TestCase):
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

        self.posts_context = []
        for nomber_post in range(1, 13):
            self.posts_context += [f'Текст тестового поста №{nomber_post}']

        for post in self.posts_context:
            Post.objects.create(
                text=post,
                group=Group.objects.get(pk=1),
                author=self.user
            )
        self.post_pk = Post.objects.get(pk=1).pk
        self.group_slug = Group.objects.get(pk=1).slug

    def test_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице равно 10.'''

        templates_pages_names = [
            reverse('posts:main_menu'),
            reverse('posts:group_list', kwargs={'slug': self.group_slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]

        for reverce in templates_pages_names:
            with self.subTest(reverce=reverce):
                response = self.client.get(reverse('posts:main_menu'))
                self.assertEqual(len(response.context['page_obj']), COUNT_PAGE)

    def test_second_page_contains_three_records(self):
        '''Проверка: на второй странице должно быть три поста.'''

        templates_pages_names = [
            reverse('posts:main_menu'),
            reverse('posts:group_list', kwargs={'slug': self.group_slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]

        for reverce in templates_pages_names:
            with self.subTest(reverce=reverce):
                response = self.client.get(
                    reverse('posts:main_menu') + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    (len(self.posts_context) - COUNT_PAGE)
                )


class GroupRedirectTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is test description'
        )

        Group.objects.create(
            title='Test group №2',
            slug='test2_slug',
            description='This is test 2 description'
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

        self.post = Post.objects.get(text='Test post text')
        self.post_pk = Post.objects.get(pk=1).pk
        self.group_slug = Group.objects.get(pk=1).slug
        self.group_no_right_slug = Group.objects.get(pk=2).slug

    def test_pages_uses_correct_template(self):
        """Проверяем, что вьюхи используют правильные шаблоны."""
        templates_pages_names = {
            reverse('posts:main_menu'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post_pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post_pk}
            ): 'posts/create_post.html',
        }

        for revers_name, templates in templates_pages_names.items():
            with self.subTest(revers_name=revers_name):
                response = self.authorized_client.get(revers_name)
                self.assertTemplateUsed(response, templates)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(
                        reverse(
                            'posts:post_detail',
                            kwargs={'post_id': self.post_pk}
                        )))
        self.assertEqual(response.context.get('post').text, 'Test post text')
        self.assertEqual(
            response.context.get('post').group,
            Group.objects.get(
                pk=1))
        self.assertEqual(response.context.get('post').author, self.user)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse(
                        'posts:group_list',
                        kwargs={'slug': self.group_slug}
                    )))
        self.assertEqual(
            response.context.get('group'),
            Group.objects.get(
                slug=self.group_slug))

    def test_create_post_show_correct_context(self):
        """При создании поста указать группу, то этот пост появляется на
        главной странице сайта, на странице выбранной группы, в профайле
        пользователя."""
        templates_pages_names = {
            reverse('posts:main_menu'),
            reverse('posts:group_list', kwargs={'slug': self.group_slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }

        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                # first_object = response.context['object_list'][0]
                self.assertEqual(
                    response.context['page_obj'][0],
                    self.post
                )

    def test_create_post_show_in_allen_group(self):
        """При создании поста указать группу, то этот пост не появляется на
        странице другой группы."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_no_right_slug}
            )
        )
        self.assertNotEqual(
            response.context.get('post'),
            Post.objects.get(
                text='Test post text'))


class CasheTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='User_test')
        cls.post_cash = Post.objects.create(
            author=cls.user,
            text='Тестируем cashe',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_page(self):
        response = self.authorized_client.get(
            reverse('posts:main_menu')).context
        self.post_cash.delete()
        response_cache = self.authorized_client.get(
            reverse('posts:main_menu')).context
        self.assertEqual(response, response_cache)
        cache.clear()
        response_clear = self.authorized_client.get(
            reverse('posts:main_menu')).context
        self.assertNotEqual(response, response_clear)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskContextImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='This is test description'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        Post.objects.create(
            text='Test post text',
            group=Group.objects.get(pk=1),
            author=self.user,
            image=self.uploaded
        )

        self.post = Post.objects.get(pk=1)

    def test_create_task(self):
        """В контексте передается картинка."""

        templates_pages_names = [
            # reverse('posts:main_menu'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            # reverse('posts:group_list', kwargs={
            # 'slug': TaskContextImageTests.group.slug}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        ]

        for revers_name in templates_pages_names:
            with self.subTest(revers_name=revers_name):
                response = (self.authorized_client.
                            get(revers_name))

                self.assertEqual(response.context.get(
                    'post').image, f'posts/{self.uploaded.name}')

    def test_create_task2(self):
        """В контексте передается картинка."""

        templates_pages_names = [
            reverse('posts:main_menu'),
            # reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:group_list', kwargs={
                    'slug': TaskContextImageTests.group.slug}),
            # reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        ]

        for revers_name in templates_pages_names:
            with self.subTest(revers_name=revers_name):
                response = (self.authorized_client.
                            get(revers_name))

                self.assertEqual(
                    response.context['page_obj'][0].image,
                    f'posts/{self.uploaded.name}')
