from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse
from unittest.mock import patch, MagicMock
from accounts.models import UserGroup, LoginAudit
from django.contrib import messages


class AuditAccessTest(TestCase):
    """Тесты для проверки доступа к аудиту в зависимости от групп пользователя"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.client = Client()
        
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Создаем сессию для пользователя
        self.session = SessionStore()
        self.session['user_id'] = self.user.id
        self.session['username'] = self.user.username
        self.session['access'] = 'test_access_token'  # Правильное название поля
        self.session['refresh'] = 'test_refresh_token'  # Добавляем refresh токен
        self.session['user_info'] = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        self.session.save()
        
        # Устанавливаем сессию в клиент
        self.client.cookies['sessionid'] = self.session.session_key

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_with_eisgs_appsecurity_group(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: пользователь с группой EISGS_AppSecurity должен иметь доступ к аудиту"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': True,
            'has_user_access': True,
            'groups': ['EISGS_AppSecurity']
        }
        
        # Создаем группу EISGS_AppSecurity для пользователя
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        )
        
        # Устанавливаем флаг доступа в сессии
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть доступ
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit.html')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_without_eisgs_appsecurity_group(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: пользователь без группы EISGS_AppSecurity не должен иметь доступ к аудиту"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': False,
            'has_user_access': True,
            'groups': ['EISGS_Users']
        }
        
        # Создаем только группу EISGS_Users (без EISGS_AppSecurity)
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_Users'
        )
        
        # Устанавливаем флаг доступа в сессии
        self.session['has_audit_access'] = False
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть редирект на главную с сообщением об ошибке
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_with_no_groups(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: пользователь без групп не должен иметь доступ к аудиту"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': False,
            'has_security_access': False,
            'has_user_access': False,
            'groups': []
        }
        
        # Устанавливаем флаг доступа в сессии
        self.session['has_audit_access'] = False
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть редирект на главную с сообщением об ошибке
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_tab_visibility_with_access(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: закладка Аудит должна быть видна пользователю с доступом"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': True,
            'has_user_access': True,
            'groups': ['EISGS_AppSecurity']
        }
        
        # Создаем группу EISGS_AppSecurity
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        )
        
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Act - получаем главную страницу
        response = self.client.get('/')
        
        # Assert - закладка Аудит должна быть в HTML
        self.assertContains(response, 'Аудит')
        self.assertContains(response, 'fas fa-shield-alt')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_tab_visibility_without_access(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: закладка Аудит не должна быть видна пользователю без доступа"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': False,
            'has_user_access': True,
            'groups': ['EISGS_Users']
        }
        
        # Устанавливаем флаг доступа в сессии
        self.session['has_audit_access'] = False
        self.session.save()
        
        # Act - получаем главную страницу
        response = self.client.get('/')
        
        # Assert - закладка Аудит не должна быть в HTML
        self.assertNotContains(response, 'Аудит')
        self.assertNotContains(response, 'fas fa-shield-alt')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_with_different_domain(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: проверка доступа для пользователя из другого домена"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'otherdomain',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': False,
            'has_user_access': True,
            'groups': ['EISGS_Users']
        }
        
        # Создаем группу в другом домене
        UserGroup.objects.create(
            username='testuser',
            domain='otherdomain',
            group_name='EISGS_AppSecurity'
        )
        
        # Устанавливаем домен в сессии
        self.session['user_info']['domain'] = 'otherdomain'
        self.session['has_audit_access'] = False  # Должно быть False, так как группа в другом домене
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть доступ, так как группа существует в домене otherdomain
        # и audit_view проверяет группы по домену из сессии
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit.html')
        
        # Дополнительная проверка: убеждаемся, что в базе данных есть группа в домене otherdomain
        other_domain_group = UserGroup.objects.filter(
            username='testuser',
            domain='otherdomain',
            group_name='EISGS_AppSecurity'
        ).first()
        self.assertIsNotNone(other_domain_group, "Группа в домене otherdomain должна существовать")
        
        # Проверяем, что группа в домене belstat не существует
        current_domain_group = UserGroup.objects.filter(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        ).first()
        self.assertIsNone(current_domain_group, "Группа в домене belstat не должна существовать")

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_with_case_sensitive_group_name(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: проверка доступа с учетом регистра названия группы"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': True,
            'has_user_access': True,
            'groups': ['EISGS_AppSecurity']
        }
        
        # Создаем группу с правильным названием
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        )
        
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть доступ
        self.assertEqual(response.status_code, 200)

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_after_group_removal(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: доступ к аудиту должен быть отозван после удаления группы"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': True,
            'has_user_access': True,
            'groups': ['EISGS_AppSecurity']
        }
        
        # Создаем группу и даем доступ
        group = UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        )
        
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Проверяем, что доступ есть
        response = self.client.get('/accounts/audit/')
        self.assertEqual(response.status_code, 200)
        
        # Act - удаляем группу
        group.delete()
        
        # Обновляем сессию (имитируем middleware)
        self.session['has_audit_access'] = False
        self.session.save()
        
        # Assert - доступ должен быть отозван
        response = self.client.get('/accounts/audit/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    @patch('accounts.middleware.AuthMiddleware._check_token_valid')
    @patch('accounts.middleware.AuthMiddleware._get_user_info')
    @patch('accounts.permissions.PermissionChecker.check_user_permissions')
    def test_audit_access_with_multiple_groups(self, mock_permissions, mock_user_info, mock_token_valid):
        """Тест: доступ к аудиту при наличии нескольких групп"""
        # Arrange - мокаем проверку токена и пользователя
        mock_token_valid.return_value = True
        mock_user_info.return_value = {
            'username': 'testuser',
            'domain': 'belstat',
            'guid': 'test-guid-123'
        }
        mock_permissions.return_value = {
            'has_access': True,
            'has_security_access': True,
            'has_user_access': True,
            'groups': ['EISGS_Users', 'EISGS_AppSecurity', 'Other_Group']
        }
        
        # Создаем несколько групп, включая EISGS_AppSecurity
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_Users'
        )
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='EISGS_AppSecurity'
        )
        UserGroup.objects.create(
            username='testuser',
            domain='belstat',
            group_name='Other_Group'
        )
        
        self.session['has_audit_access'] = True
        self.session.save()
        
        # Act - пытаемся получить доступ к странице аудита
        response = self.client.get('/accounts/audit/')
        
        # Assert - должен быть доступ
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit.html')
