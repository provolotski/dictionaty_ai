"""
Тесты для получения содержимого справочника
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore

from api.views import get_dictionary_content


class TestDictionaryContent(TestCase):
    """Тесты для получения содержимого справочника"""

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
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session.save()
        
        self.client.cookies['sessionid'] = self.session.session_key

    def test_get_dictionary_content_success(self):
        """Тест успешного получения содержимого справочника"""
        # Arrange
        dictionary_id = 1
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    'id': 1,
                    'code': 'POS001',
                    'name': 'Позиция 1',
                    'description': 'Описание позиции 1',
                    'parent_code': None,
                    'start_date': '2025-01-01',
                    'end_date': '2025-12-31'
                },
                {
                    'id': 2,
                    'code': 'POS002',
                    'name': 'Позиция 2',
                    'description': 'Описание позиции 2',
                    'parent_code': 'POS001',
                    'start_date': '2025-01-01',
                    'end_date': '2025-12-31'
                }
            ]
            mock_response.content = b'[{"id": 1, "code": "POS001", "name": "Позиция 1"}, {"id": 2, "code": "POS002", "name": "Позиция 2"}]'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['code'], 'POS001')
        self.assertEqual(data[1]['code'], 'POS002')

    def test_get_dictionary_content_missing_parameter(self):
        """Тест получения содержимого без параметра dictionary"""
        # Act
        response = self.client.get('/api/v2/models/dictionary/')
        
        # Assert
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Missing required parameter: dictionary', data['error'])

    def test_get_dictionary_content_backend_error(self):
        """Тест обработки ошибки от backend"""
        # Arrange
        dictionary_id = 999
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                'error': 'Dictionary not found',
                'detail': 'Dictionary with ID 999 does not exist'
            }
            mock_response.content = b'{"error": "Dictionary not found"}'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
        
        # Assert
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_get_dictionary_content_timeout(self):
        """Тест обработки таймаута backend"""
        # Arrange
        dictionary_id = 1
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
        
        # Assert
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_get_dictionary_content_empty_response(self):
        """Тест получения пустого содержимого справочника"""
        # Arrange
        dictionary_id = 1
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.content = b'[]'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_get_dictionary_content_without_auth(self):
        """Тест получения содержимого без авторизации"""
        # Arrange
        dictionary_id = 1
        
        # Act
        response = self.client.get(f'/api/v2/models/dictionary/?dictionary={dictionary_id}')
        
        # Assert
        # Должен вернуть 200, но с предупреждением в логах
        self.assertEqual(response.status_code, 200)


class TestDictionaryContentIntegration(TestCase):
    """Интеграционные тесты для содержимого справочника"""

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
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session.save()
        
        self.client.cookies['sessionid'] = self.session.session_key

    def test_full_dictionary_content_workflow(self):
        """Полный тест рабочего процесса получения содержимого справочника"""
        # 1. Получаем содержимое справочника
        dictionary_id = 1
        
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    'id': 1,
                    'code': 'POS001',
                    'name': 'Позиция 1',
                    'description': 'Описание позиции 1',
                    'parent_code': None,
                    'start_date': '2025-01-01',
                    'end_date': '2025-12-31'
                }
            ]
            mock_response.content = b'[{"id": 1, "code": "POS001", "name": "Позиция 1"}]'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['code'], 'POS001')

    def test_dictionary_content_error_handling(self):
        """Тест обработки различных типов ошибок"""
        # Arrange
        dictionary_id = 1
        
        # Тест 1: Ошибка 500 от backend
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {'error': 'Internal server error'}
            mock_response.content = b'{"error": "Internal server error"}'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertIn('error', data)
        
        # Тест 2: Ошибка 422 от backend
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {'error': 'Validation error'}
            mock_response.content = b'{"error": "Validation error"}'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/v2/models/dictionary/?dictionary={dictionary_id}',
                HTTP_AUTHORIZATION='Bearer test_access_token'
            )
            
            self.assertEqual(response.status_code, 422)
            data = json.loads(response.content)
            self.assertIn('error', data)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
