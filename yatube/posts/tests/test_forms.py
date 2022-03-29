from http import HTTPStatus
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from ..models import Group, Post
from django.urls import reverse
import tempfile
import shutil
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='test_text',
            author_id=cls.user.id
        )

    def setUp(self):
        self.authenticated_user = Client()
        self.authenticated_user.force_login(FormTest.user)

    def test_new_object(self):
        """Проверка создания нового объекта поста"""
        posts_count = Post.objects.count()
        response = self.authenticated_user.post(reverse(
            'posts:post_create'),
            {'text': 'second_test_text'})
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        new_post = Post.objects.filter(
            text='second_test_text',
            author_id=FormTest.user.id,
            group=None)
        self.assertTrue(new_post.exists())

    def test_post_edit(self):
        """Проверка изменения отредактированного поста"""
        old_post = FormTest.post
        posts_count = Post.objects.all().count()
        self.authenticated_user.post(
            reverse('posts:post_edit', kwargs={'post_id': old_post.id}),
            {'text': 'new_text'}
        )
        self.assertEqual(posts_count, Post.objects.all().count())
        self.assertEqual(
            'new_text',
            Post.objects.get(id=FormTest.post.id).text)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test everythink'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authenticated_user = Client()
        self.authenticated_user.force_login(ImageTest.user)

    def test_image_form(self):
        """Проверка загрузки изображения и вывода"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'test_text',
            'group': ImageTest.group.id,
            'image': uploaded
        }
        response = self.authenticated_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.filter(
            text='test_text',
            group=ImageTest.group,
            image='posts/small.gif'
        )
        self.assertTrue(new_post.exists())
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': ImageTest.user.username}))
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:current_post',
                kwargs={'slug': ImageTest.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': ImageTest.user.username}),
        ]
        current_post = Post.objects.get(
            text='test_text',
            group=ImageTest.group,
            image='posts/small.gif'
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authenticated_user.get(url)
                posts = response.context.get('page_obj').object_list
                self.assertIn(current_post, posts)
        response = self.authenticated_user.get(
            reverse('posts:post_detail', kwargs={'post_id': current_post.id}))
        self.assertEqual(current_post, response.context.get('post'))
