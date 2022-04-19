from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_group_models_str_(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group_model = PostModelTest.group
        self.assertEqual(str(group_model), group_model.title)

    def test_post_models_str_(self):
        """Проверяем, что у моделей Post корректно работает __str__."""
        post_model = PostModelTest.post
        self.assertEqual(str(post_model), post_model.text[:15])
