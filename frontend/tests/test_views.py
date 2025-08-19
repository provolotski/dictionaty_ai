"""
Тесты для Django views (accounts и home)
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import get_user_model

from accounts.views import login_view, users_view, profile_view
from home.views import dictionaries_page, dictionary_create_page


@pytest.mark.frontend
@pytest.mark.views
@pytest.mark.auth
class TestAccountsViews(TestCase):
    """Тесты для views в приложении accounts"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Создаем сессию для пользователя
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Устанавливаем сессию в клиент
        self.client.cookies['sessionid'] = self.session.session_key

    def test_login_view_get(self):
        """Тест GET запроса для страницы входа"""
        # Act
        response = self.client.get('/accounts/login/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_post_success(self):
        """Тест успешного POST запроса для входа"""
        # Arrange
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        # Act
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.return_value = {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'user': {
                    'username': 'testuser',
                    'display_name': 'Test User',
                    'email': 'test@example.com',
                    'groups': ['EISGS_Users', 'EISGS_AppSecurity'],
                    'department': 'IT',
                    'title': 'Developer',
                    'employee_id': 'EMP001'
                }
            }
            
            response = self.client.post('/accounts/login/', login_data)
        
        # Assert
        self.assertEqual(response.status_code, 302)  # Редирект после успешного входа
        self.assertRedirects(response, '/')

    def test_login_view_post_invalid_credentials(self):
        """Тест POST запроса с неверными учетными данными"""
        # Arrange
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        # Act
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            
            response = self.client.post('/accounts/login/', login_data)
        
        # Assert
        self.assertEqual(response.status_code, 200)  # Остается на странице входа
        self.assertTemplateUsed(response, 'login.html')
        # Проверяем, что сообщение об ошибке передается в контекст
        self.assertIn('error_message', response.context)

    def test_users_view_authenticated_user(self):
        """Тест страницы пользователей для авторизованного пользователя"""
        # Act
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.return_value = [
                {
                    'username': 'user1',
                    'display_name': 'User One',
                    'email': 'user1@example.com',
                    'groups': ['EISGS_Users'],
                    'department': 'IT',
                    'title': 'Developer',
                    'employee_id': 'EMP001'
                },
                {
                    'username': 'user2',
                    'display_name': 'User Two',
                    'email': 'user2@example.com',
                    'groups': ['EISGS_Users', 'EISGS_AppSecurity'],
                    'department': 'HR',
                    'title': 'Manager',
                    'employee_id': 'EMP002'
                }
            ]
            
            response = self.client.get('/accounts/users/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users.html')
        self.assertIn('users', response.context)
        self.assertIn('has_audit_access', response.context)
        self.assertTrue(response.context['has_audit_access'])

    def test_users_view_unauthenticated_user(self):
        """Тест страницы пользователей для неавторизованного пользователя"""
        # Arrange - создаем клиент без сессии
        unauthenticated_client = Client()
        
        # Act
        response = unauthenticated_client.get('/accounts/users/')
        
        # Assert
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_profile_view_authenticated_user(self):
        """Тест страницы профиля для авторизованного пользователя"""
        # Act
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.return_value = {
                'username': 'testuser',
                'display_name': 'Test User',
                'email': 'test@example.com',
                'groups': ['EISGS_Users'],
                'department': 'IT',
                'title': 'Developer',
                'employee_id': 'EMP001'
            }
            
            response = self.client.get('/accounts/profile/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('user_data', response.context)

    def test_profile_view_unauthenticated_user(self):
        """Тест страницы профиля для неавторизованного пользователя"""
        # Arrange - создаем клиент без сессии
        unauthenticated_client = Client()
        
        # Act
        response = unauthenticated_client.get('/accounts/profile/')
        
        # Assert
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа


@pytest.mark.frontend
@pytest.mark.views
@pytest.mark.dictionaries
class TestHomeViews(TestCase):
    """Тесты для views в приложении home"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Создаем сессию для пользователя с правами EISGS_Users
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session.save()
        
        # Устанавливаем сессию в клиент
        self.client.cookies['sessionid'] = self.session.session_key

    def test_dictionaries_page_authenticated_user(self):
        """Тест страницы справочников для авторизованного пользователя"""
        # Act
        with patch('home.views.external_auth_api') as mock_auth:
            mock_auth.return_value = [
                {
                    'id': 1,
                    'name': 'Dictionary 1',
                    'code': 'DICT_001',
                    'description': 'Description 1',
                    'start_date': '2025-01-01',
                    'finish_date': '2025-12-31',
                    'name_eng': 'Dictionary 1',
                    'name_bel': 'Dictionary 1',
                    'description_eng': 'Description 1',
                    'description_bel': 'Description 1',
                    'gko': 'GKO1',
                    'organization': 'Org1',
                    'classifier': 'Class1',
                    'id_type': 0,
                    'id_status': 1,
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                },
                {
                    'id': 2,
                    'name': 'Dictionary 2',
                    'code': 'DICT_002',
                    'description': 'Description 2',
                    'start_date': '2025-01-01',
                    'finish_date': '2025-12-31',
                    'name_eng': 'Dictionary 2',
                    'name_bel': 'Dictionary 2',
                    'description_eng': 'Description 2',
                    'description_bel': 'Description 2',
                    'gko': 'GKO2',
                    'organization': 'Org2',
                    'classifier': 'Class2',
                    'id_type': 1,
                    'id_status': 1,
                    'created_at': '2025-01-01T00:00:00',
                    'updated_at': '2025-01-01T00:00:00'
                }
            ]
            
            response = self.client.get('/dictionaries/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dictionaries.html')
        self.assertIn('dictionaries', response.context)
        dictionaries = response.context['dictionaries']
        self.assertEqual(len(dictionaries), 2)
        self.assertEqual(dictionaries[0]['name'], 'Dictionary 1')
        self.assertEqual(dictionaries[1]['name'], 'Dictionary 2')

    def test_dictionaries_page_unauthenticated_user(self):
        """Тест страницы справочников для неавторизованного пользователя"""
        # Arrange - создаем клиент без сессии
        unauthenticated_client = Client()
        
        # Act
        response = unauthenticated_client.get('/dictionaries/')
        
        # Assert
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_dictionary_create_page_authenticated_user(self):
        """Тест страницы создания справочника для авторизованного пользователя"""
        # Act
        response = self.client.get('/dictionaries/create/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dictionary_create.html')
        self.assertIn('access_token', response.context)
        self.assertEqual(response.context['access_token'], 'test_access_token')

    def test_dictionary_create_page_unauthenticated_user(self):
        """Тест страницы создания справочника для неавторизованного пользователя"""
        # Arrange - создаем клиент без сессии
        unauthenticated_client = Client()
        
        # Act
        response = unauthenticated_client.get('/dictionaries/create/')
        
        # Assert
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_home_page_authenticated_user(self):
        """Тест главной страницы для авторизованного пользователя"""
        # Act
        response = self.client.get('/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_unauthenticated_user(self):
        """Тест главной страницы для неавторизованного пользователя"""
        # Arrange - создаем клиент без сессии
        unauthenticated_client = Client()
        
        # Act
        response = unauthenticated_client.get('/')
        
        # Assert
        self.assertEqual(response.status_code, 200)  # Главная страница доступна всем


@pytest.mark.frontend
@pytest.mark.integration
class TestViewsIntegration(TestCase):
    """Интеграционные тесты для views"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Создаем сессию для пользователя
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session['has_audit_access'] = True
        self.session.save()
        
        self.client.cookies['sessionid'] = self.session.session_key

    def test_full_user_journey(self):
        """Полный тест пользовательского пути"""
        # 1. Вход в систему
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.return_value = {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'user': {
                    'username': 'testuser',
                    'display_name': 'Test User',
                    'email': 'test@example.com',
                    'groups': ['EISGS_Users', 'EISGS_AppSecurity'],
                    'department': 'IT',
                    'title': 'Developer',
                    'employee_id': 'EMP001'
                }
            }
            
            login_response = self.client.post('/accounts/login/', login_data)
            self.assertEqual(login_response.status_code, 302)
        
        # 2. Переход на главную страницу
        home_response = self.client.get('/')
        self.assertEqual(home_response.status_code, 200)
        
        # 3. Переход на страницу справочников
        with patch('home.views.external_auth_api') as mock_auth:
            mock_auth.return_value = []
            
            dict_response = self.client.get('/dictionaries/')
            self.assertEqual(dict_response.status_code, 200)
        
        # 4. Переход на страницу создания справочника
        create_response = self.client.get('/dictionaries/create/')
        self.assertEqual(create_response.status_code, 200)
        
        # 5. Переход на страницу пользователей
        with patch('accounts.views.external_auth_api') as mock_auth:
            mock_auth.return_value = []
            
            users_response = self.client.get('/accounts/users/')
            self.assertEqual(users_response.status_code, 200)

    def test_user_permissions_workflow(self):
        """Тест рабочего процесса с проверкой прав пользователя"""
        # 1. Проверяем доступ к защищенным страницам
        protected_pages = [
            '/dictionaries/',
            '/dictionaries/create/',
            '/accounts/users/',
            '/accounts/profile/'
        ]
        
        for page in protected_pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200, f"Страница {page} недоступна")
        
        # 2. Проверяем доступ к публичным страницам
        public_pages = ['/', '/accounts/login/']
        
        for page in public_pages:
            response = self.client.get(page)
            self.assertIn(response.status_code, [200, 302], f"Страница {page} недоступна")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
