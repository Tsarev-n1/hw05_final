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
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post_str = PostModelTest.post.text[:15]
        group_str = PostModelTest.group.title
        self.assertEqual(post_str, str(PostModelTest.post),
                         'Проблема в __str__ модели Post')
        self.assertEqual(group_str, str(PostModelTest.group),
                         'Проблема в __str__ модели Group')
