from django.test import TestCase
from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Проверка ответа на 404"""
        response = self.client.get('/nonexist-page/')
        # Проверьте, что статус ответа сервера - 404
        # Проверьте, что используется шаблон core/404.html
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_error(self):
        """Проверка шаблона на 404"""
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
