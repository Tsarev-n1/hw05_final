from django.urls import reverse
from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from http import HTTPStatus


User = get_user_model()


class DynamicUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test_group',
            slug='test_group',
            description='test everythink'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='Test',
            author_id=cls.user.id,
            group=cls.group
        )
        cls.post_id = cls.post.id

    def setUp(self):
        self.guest_user = Client()
        self.aunteticated_user = Client()
        self.aunteticated_user.force_login(DynamicUrlTests.user)

    def test_available_all(self):
        """Проверка доступности страниц неавторизованному пользователю"""
        urls = ['/', '/group/test_group/', '/profile/test_user/',
                '/posts/' + str(DynamicUrlTests.post_id) + '/']
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_aviable_author(self):
        """Проверка доступности редактирования записи автору"""
        url = '/posts/' + str(DynamicUrlTests.post_id) + '/edit/'
        response = self.aunteticated_user.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_aviable_autheticated(self):
        """Проверка доступа к странице авторизированным пользователям"""
        url = '/create/'
        response = self.aunteticated_user.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_exist(self):
        """Проверка несуществующих страниц"""
        url = '/unexisting_page/'
        response = self.guest_user.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_used_templates(self):
        """Проверка использованных шаблонов"""
        post_url = '/posts/' + str(DynamicUrlTests.post_id) + '/'
        templates = {
            '/': 'posts/index.html',
            '/group/test_group/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            post_url: 'posts/post_detail.html',
            (post_url + 'edit/'): 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for url, template in templates.items():
            with self.subTest(url=url):
                response = self.aunteticated_user.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirect(self):
        """Проверка редиректа после редактирования поста"""
        response = self.aunteticated_user.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': DynamicUrlTests.post_id}),
            {'text': 'new_text'}, follow=True)
        self.assertRedirects(response, (reverse(
            'posts:post_detail',
            kwargs={'post_id': DynamicUrlTests.post_id})))

    def test_guest_edit_redirect(self):
        """Проверка редиректа неавторизированного пользователя"""
        response = self.guest_user.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}),
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))
