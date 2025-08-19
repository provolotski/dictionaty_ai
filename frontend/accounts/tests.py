from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
import json


class GetAccessTokenTestCase(TestCase):
    """Тесты для endpoint получения токена доступа"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Создаем сессию для пользователя
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access'] = 'test_access_token_123'
        self.session['in_users'] = True
        self.session.save()
        
        # Устанавливаем сессию в клиент
        self.client.cookies['sessionid'] = self.session.session_key
        
        # Аутентифицируем пользователя в Django через сессию
        self.client.session['_auth_user_id'] = self.user.id
        self.client.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        self.client.session.save()

    def test_get_access_token_authenticated(self):
        """Тест получения токена для аутентифицированного пользователя"""
        response = self.client.get('/accounts/get_access_token/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_token', data)
        self.assertEqual(data['access_token'], 'test_access_token_123')
        self.assertEqual(data['status_code'], 200)

    def test_get_access_token_not_authenticated(self):
        """Тест получения токена для неаутентифицированного пользователя"""
        # Создаем клиент без сессии
        client = Client()
        response = client.get('/accounts/get_access_token/')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['status_code'], 401)

    def test_get_access_token_no_token_in_session(self):
        """Тест получения токена когда токен отсутствует в сессии"""
        # Создаем сессию без токена
        session = SessionStore()
        session['user_id'] = self.user.id
        session['username'] = self.user.username
        session['in_users'] = True
        session.save()
        
        client = Client()
        client.cookies['sessionid'] = session.session_key
        
        # Аутентифицируем пользователя в Django через сессию
        client.session['_auth_user_id'] = self.user.id
        client.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        client.session.save()
        
        response = client.get('/accounts/get_access_token/')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['status_code'], 404)
