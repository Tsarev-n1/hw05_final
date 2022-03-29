from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django import forms
from ..models import Follow, Post, Group, Comment
from django.urls import reverse


User = get_user_model()


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
        expected = Post.objects.filter(author_id=ContextTest.user.id)[:10]
        response = self.authenticated_user.get(reverse(
            'posts:profile',
            kwargs={'username': 'test_user'})
        )
        value = response.context['page_obj'].object_list
        self.assertEqual(list(expected), value)

    def test_post_detail(self):
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
        """Проверка наличия поста в грппе и его отсутвие в другой"""
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
        CacheTest.new_post.delete()
        self.assertIn('test_text', str(response.content))


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
        """Проверка подписки и отписки авторизированного пользователя"""
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
