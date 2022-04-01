from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django import forms
from ..models import Follow, Post, Group, Comment
from django.urls import reverse
import tempfile
import shutil
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class TemplateViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Test_group',
            slug='test_group',
            description='test everythink'
        )
        cls.post = Post.objects.create(
            text='Test',
            author_id=cls.user.id,
            group=cls.group
        )

    def setUp(self):
        self.authenticated_user = Client()
        self.authenticated_user.force_login(TemplateViewsTest.user)

    def test_templates(self):
        """Проверка шаблонов в views"""
        post_id = str(TemplateViewsTest.post.id)
        lib = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list'): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'test_user'}): (
                'posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': post_id}): (
                'posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={'post_id': post_id}): (
                'posts/post_create.html'),
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for url, template in lib.items():
            with self.subTest(url=url):
                response = self.authenticated_user.get(url)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_group',
            description='test everythink'
        )
        articles = []
        for i in range(12):
            articles.append(Post(
                text=('Test_text' + str(i)),
                group=cls.group,
                author_id=cls.user.id))
        Post.objects.bulk_create(articles)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authenticated_user = Client()
        self.authenticated_user.force_login(ContextTest.user)

    def test_paginator_count(self):
        """Проверка паджинатора"""
        lib = {
            reverse('posts:index'): 10,
            reverse('posts:index') + '?page=2': 2,
            reverse('posts:current_post',
                    kwargs={'slug': 'test_group'}): 10,
            reverse('posts:current_post',
                    kwargs={'slug': 'test_group'}) + '?page=2': 2,
            reverse('posts:profile',
                    kwargs={'username': ContextTest.user}): 10,
            reverse('posts:profile',
                    kwargs={'username': ContextTest.user}) + (
                '?page=2'): 2,
        }
        for url, count in lib.items():
            with self.subTest(url=url):
                response = self.authenticated_user.get(url)
                self.assertEqual(len(response.context['page_obj']), count)

    def test_group_list_posts(self):
        """Проверка фильтрации постов в group_list"""
        expected = Post.objects.filter(group=ContextTest.group)[:10]
        response = self.authenticated_user.get(reverse('posts:current_post',
                                               kwargs={'slug': 'test_group'}))
        value = response.context['page_obj'].object_list
        self.assertEqual(list(expected), value)

    def test_profile_posts(self):
        """Проверка постов в профиле"""
        expected = Post.objects.filter(author_id=ContextTest.user.id)[:10]
        response = self.authenticated_user.get(reverse(
            'posts:profile',
            kwargs={'username': 'test_user'})
        )
        value = response.context['page_obj'].object_list
        self.assertEqual(list(expected), value)

    def test_post_detail(self):
        """Проверка конкретного поста"""
        expected = Post.objects.get(id=1)
        response = self.authenticated_user.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        value = response.context['post']
        self.assertEqual(expected, value)

    def test_post_edit(self):
        """Проверка страницы edit"""
        post = Post.objects.get(id=1)
        response = self.authenticated_user.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        dict = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for name, value in dict.items():
            with self.subTest(name=name):
                form_field = response.context.get('form').fields.get(name)
                self.assertIsInstance(form_field, value)
        form_field = response.context.get('form')
        form_data = {
            form_field.instance.text: post.text,
            form_field.instance.group: post.group,
        }
        for name, value in form_data.items():
            '#Проверка наличия данных в форме'
            with self.subTest(name=name):
                result = name
                self.assertEqual(value, result)

    def test_create_post(self):
        """Проверка формы создания поста"""
        response = self.authenticated_user.get(reverse('posts:post_create'))
        dict = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for name, value in dict.items():
            with self.subTest(name=name):
                form_field = response.context.get('form').fields.get(name)
                self.assertIsInstance(form_field, value)

    def test_post_views_pages(self):
        """Проверка наличия поста в профиле, группе, на главное странице"""
        new_post = Post.objects.create(
            text='tests',
            group=ContextTest.group,
            author_id=ContextTest.user.id
        )
        check_list = {
            'Главная': reverse('posts:index'),
            'Профиль': reverse('posts:profile',
                               kwargs={'username': 'test_user'}),
            'Группа': reverse('posts:current_post',
                              kwargs={'slug': 'test_group'}),
        }
        for name, page in check_list.items():
            with self.subTest(name=name):
                response = self.authenticated_user.get(page)
                page_obj = response.context.get('page_obj').object_list
                self.assertIn(new_post, page_obj)

    def test_post_another_group(self):
        """Проверка наличия поста в группе и его отсутвие в другой"""
        new_group = Group.objects.create(
            title='Second_test_group',
            slug='second_group',
            description='test everythink'
        )
        new_post = Post.objects.create(
            text='other post',
            author_id=ContextTest.user.id,
            group=new_group
        )
        response = self.authenticated_user.get(
            reverse(
                'posts:current_post',
                kwargs={'slug': 'second_group'})
        )
        posts = response.context.get('page_obj').object_list
        response_other_group = self.authenticated_user.get(
            reverse(
                'posts:current_post',
                kwargs={'slug': 'test_group'}
            )
        )
        other_group = response_other_group.context.get('page_obj').object_list
        self.assertIn(new_post, posts)
        self.assertNotIn(new_post, other_group)

    def test_image_pages(self):
        """Проверка наличия изображения на страницах"""
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
            'group': ContextTest.group.id,
            'image': uploaded
        }
        self.authenticated_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.get(
            text='test_text',
            group=ContextTest.group,
            image='posts/small.gif'
        )
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': ContextTest.user}
            ),
            reverse(
                'posts:current_post',
                kwargs={'slug': ContextTest.group.slug}
            )
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authenticated_user.get(url)
                page_obj = response.context.get('page_obj').object_list
                self.assertIn(new_post, page_obj)
        post_detail_response = self.authenticated_user.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': new_post.id}
            )
        )
        post_detail_post = post_detail_response.context.get('post')
        self.assertEqual(new_post, post_detail_post)


class CommentsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.new_post = Post.objects.create(
            text='test_text',
            author_id=cls.user.id
        )

    def setUp(self):
        self.guest = Client()
        self.authenticated_user = Client()
        self.authenticated_user.force_login(CommentsTest.user)

    def test_comment_create(self):
        """Проверка создания комментария и редиректа"""
        context = {'text': 'test_comment'}
        response = self.authenticated_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentsTest.new_post.id}),
            data=context,
            follow=True
        )
        new_comment = Comment.objects.filter(text='test_comment')
        self.assertTrue(new_comment.exists())
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentsTest.new_post.id})
        )
        new_response = self.authenticated_user.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': CommentsTest.new_post.id}
            )
        )
        comment = new_response.context.get('comments')
        self.assertEqual(list(new_comment), list(comment))

    def test_guest_comment_create(self):
        """Проверка создания комментария неавторзированным пользователем"""
        response = self.guest.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentsTest.new_post.id},
            ),
            data={'text': 'second_comment'},
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/comment/'))
        comment = Comment.objects.filter(text='second_comment')
        self.assertFalse(comment.exists())


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.new_post = Post.objects.create(
            text='test_text',
            author_id=CacheTest.user.id
        )

    def setUp(self):
        self.authenticated_user = Client()
        self.authenticated_user.force_login(CacheTest.user)

    def test_index_cache(self):
        """Проверка работы кеширования на главной странице"""
        response = self.authenticated_user.get(reverse('posts:index'))
        self.assertIn('test_text', str(response.content))
        CacheTest.new_post.delete()
        response = self.authenticated_user.get(reverse('posts:index'))
        self.assertIn('test_text', str(response.content))
        cache.clear()
        response = self.authenticated_user.get(reverse('posts:index'))
        self.assertNotIn('test_text', str(response.content))


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='first_user')
        cls.second_user = User.objects.create_user(username='second_user')
        cls.new_post = Post.objects.create(
            text='test_text',
            author_id=cls.first_user.id
        )

    def setUp(self):
        self.first_user = Client()
        self.first_user.force_login(FollowTest.first_user)
        self.second_user = Client()
        self.second_user.force_login(FollowTest.second_user)

    def test_user_follow(self):
        """Проверка подписки"""
        follow_response = self.second_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTest.first_user}
        ), follow=True)
        follow_index_response = self.second_user.get(
            reverse('posts:follow_index')
        )
        follow = Follow.objects.filter(
            user=FollowTest.second_user,
            author=FollowTest.first_user
        )
        self.assertTrue(follow.exists())
        self.assertIn(
            FollowTest.new_post.text,
            str(follow_index_response.content)
        )
        self.assertRedirects(follow_response, '/follow/')

    def test_user_unfollow(self):
        """Проверка отписки"""
        self.second_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTest.first_user}
        ), follow=True)
        unfollow_response = self.second_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowTest.first_user}
        ), follow=True)
        deleted_follow = Follow.objects.filter(
            user=FollowTest.second_user,
            author=FollowTest.first_user
        )
        follow_index_response = self.second_user.get(
            reverse('posts:follow_index')
        )
        self.assertFalse(deleted_follow.exists())
        self.assertNotIn(
            FollowTest.new_post.text,
            str(follow_index_response.content)
        )
        self.assertRedirects(unfollow_response, '/follow/')

    def test_follow_index(self):
        """Проверка страницы подсписок"""
        self.second_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowTest.first_user}
            )
        )
        follow_response = self.second_user.get(reverse('posts:follow_index'))
        unfollow_response = self.first_user.get(reverse('posts:follow_index'))
        self.assertIn(
            FollowTest.new_post.text,
            str(follow_response.content)
        )
        self.assertNotIn(
            FollowTest.new_post.text,
            str(unfollow_response.content)
        )
