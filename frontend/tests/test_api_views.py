"""
Тесты для Django API views
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

from api.views import proxy_api_request, create_dictionary


@pytest.mark.frontend
@pytest.mark.api
class TestAPIViews(TestCase):
    """Тесты для API views"""

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
        self.session.save()
        
        # Устанавливаем сессию в клиент
        self.client.cookies['sessionid'] = self.session.session_key

    def test_proxy_api_request_get_success(self):
        """Тест успешного GET запроса через прокси"""
        # Arrange
        url = 'v2/models/list'
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{'id': 1, 'name': 'Test'}]
            mock_response.content = b'[{"id": 1, "name": "Test"}]'
            mock_get.return_value = mock_response
            
            response = self.client.get(f'/api/{url}')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test')

    def test_proxy_api_request_post_success(self):
        """Тест успешного POST запроса через прокси"""
        # Arrange
        url = 'v2/models/newDictionary'
        data = {
            'name': 'Test Dictionary',
            'code': 'TEST001',
            'description': 'Test description'
        }
        
        # Act
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'message': 'Created', 'id': 123}
            mock_response.content = b'{"message": "Created", "id": 123}'
            mock_post.return_value = mock_response
            
            response = self.client.post(
                f'/api/{url}',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # Assert
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Created')
        self.assertEqual(data['id'], 123)

    def test_proxy_api_request_error_handling(self):
        """Тест обработки ошибок в прокси"""
        # Arrange
        url = 'v2/models/list'
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = 'Internal Server Error'
            mock_response.content = b'Internal Server Error'
            mock_get.return_value = mock_response
            
            response = self.client.get(f'/api/{url}')
        
        # Assert
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_create_dictionary_success(self):
        """Тест успешного создания справочника"""
        # Arrange
        data = {
            'name': 'Test Dictionary',
            'code': 'TEST001',
            'description': 'Test description',
            'start_date': '2025-08-18',
            'finish_date': '9999-12-31',
            'id_type': '0'
        }
        
        # Act
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'message': 'Created', 'id': 123}
            mock_response.content = b'{"message": "Created", "id": 123}'
            mock_post.return_value = mock_response
            
            response = self.client.post(
                '/api/v2/models/newDictionary',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # Assert
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Created')
        self.assertEqual(data['id'], 123)

    def test_create_dictionary_missing_required_fields(self):
        """Тест создания справочника с отсутствующими обязательными полями"""
        # Arrange
        data = {
            'name': '',  # Пустое имя - недопустимо
            'code': 'TEST001'
        }
        
        # Act
        response = self.client.post(
            '/api/v2/models/newDictionary',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('missing_fields', data)

    def test_create_dictionary_backend_error(self):
        """Тест обработки ошибки от backend при создании справочника"""
        # Arrange
        data = {
            'name': 'Test Dictionary',
            'code': 'TEST001',
            'description': 'Test description',
            'start_date': '2025-08-18',
            'finish_date': '9999-12-31',
            'id_type': '0'
        }
        
        # Act
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                'detail': [{
                    'type': 'missing',
                    'loc': ['body', 'field'],
                    'msg': 'Field required'
                }]
            }
            mock_response.content = b'{"detail": [{"type": "missing", "loc": ["body", "field"], "msg": "Field required"}]}'
            mock_post.return_value = mock_response
            
            response = self.client.post(
                '/api/v2/models/newDictionary',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # Assert
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('validation_errors', data)

    def test_create_dictionary_automatic_defaults(self):
        """Тест автоматического добавления значений по умолчанию"""
        # Arrange
        data = {
            'name': 'Test Dictionary',
            'code': 'TEST001'
            # Отсутствуют start_date, finish_date, id_type, description
        }
        
        # Act
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'message': 'Created', 'id': 123}
            mock_response.content = b'{"message": "Created", "id": 123}'
            mock_post.return_value = mock_response
            
            response = self.client.post(
                '/api/v2/models/newDictionary',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # Assert
        self.assertEqual(response.status_code, 201)
        # Проверяем, что backend получил данные с значениями по умолчанию
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        sent_data = json.loads(call_args[1]['json'])
        self.assertIn('start_date', sent_data)
        self.assertIn('finish_date', sent_data)
        self.assertIn('id_type', sent_data)
        self.assertIn('description', sent_data)

    def test_proxy_api_request_with_headers(self):
        """Тест прокси с передачей заголовков"""
        # Arrange
        url = 'v2/models/list'
        
        # Act
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.content = b'[]'
            mock_get.return_value = mock_response
            
            response = self.client.get(
                f'/api/{url}',
                HTTP_AUTHORIZATION='Bearer test_token',
                HTTP_ACCEPT='application/json'
            )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        # Проверяем, что заголовки переданы в backend
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        headers = call_args[1]['headers']
        self.assertIn('Authorization', headers)
        self.assertIn('Accept', headers)


@pytest.mark.frontend
@pytest.mark.integration
class TestAPIViewsIntegration(TestCase):
    """Интеграционные тесты для API views"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Создаем сессию
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access_token'] = 'test_access_token'
        self.session['in_users'] = True
        self.session.save()
        
        self.client.cookies['sessionid'] = self.session.session_key

    def test_full_dictionary_workflow(self):
        """Полный тест рабочего процесса создания справочника"""
        # 1. Получение списка справочников
        with patch('api.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {'id': 1, 'name': 'Existing Dictionary', 'code': 'EXIST001'}
            ]
            mock_response.content = b'[{"id": 1, "name": "Existing Dictionary", "code": "EXIST001"}]'
            mock_get.return_value = mock_response
            
            list_response = self.client.get('/api/v2/models/list')
            self.assertEqual(list_response.status_code, 200)
            
            data = json.loads(list_response.content)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'Existing Dictionary')
        
        # 2. Создание нового справочника
        new_dict_data = {
            'name': 'New Test Dictionary',
            'code': 'NEW001',
            'description': 'New test description'
        }
        
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'message': 'Created', 'id': 2}
            mock_response.content = b'{"message": "Created", "id": 2}'
            mock_post.return_value = mock_response
            
            create_response = self.client.post(
                '/api/v2/models/newDictionary',
                data=json.dumps(new_dict_data),
                content_type='application/json'
            )
            self.assertEqual(create_response.status_code, 201)
            
            data = json.loads(create_response.content)
            self.assertEqual(data['id'], 2)

    def test_error_handling_workflow(self):
        """Тест рабочего процесса обработки ошибок"""
        # 1. Попытка создания справочника с неверными данными
        invalid_data = {
            'name': '',  # Пустое имя
            'code': 'INVALID'
        }
        
        response = self.client.post(
            '/api/v2/models/newDictionary',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('missing_fields', data)
        
        # 2. Попытка создания справочника с дублирующимся кодом
        duplicate_data = {
            'name': 'Duplicate Dictionary',
            'code': 'EXIST001',  # Код уже существует
            'description': 'Duplicate description',
            'start_date': '2025-08-18',
            'finish_date': '9999-12-31',
            'id_type': '0'
        }
        
        with patch('api.views.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'detail': 'Код справочника уже существует'
            }
            mock_response.content = b'{"detail": "Code already exists"}'
            mock_post.return_value = mock_response
            
            response = self.client.post(
                '/api/v2/models/newDictionary',
                data=json.dumps(duplicate_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertIn('error', data)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
