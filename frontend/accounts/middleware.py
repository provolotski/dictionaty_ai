import logging
import requests
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from .utils import log_auth_event, log_system_event

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Используем настройки из Django settings вместо хардкода
        self.auth_api_base = getattr(settings, 'AUTH_CONFIG', {}).get('EXTERNAL_API', {}).get('BASE_URL', 'http://127.0.0.1:9090/api/v1/auth')
        
        # URL-адреса, которые не требуют авторизации
        self.exempt_urls = [
            '/login/',
            '/accounts/login/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # URL-адреса, которые требуют группы EISGS_Users
        self.users_required_urls = [
            '/dictionaries',
            '/search',
            '/import',
            '/export',
            '/analytics',
        ]

    def __call__(self, request):
        # Проверяем, требует ли URL авторизации
        if not self._requires_auth(request.path):
            response = self.get_response(request)
            return response

        # Проверяем авторизацию пользователя
        if not self._is_authenticated(request):
            ip_address = self._get_client_ip(request)
            log_auth_event(
                'middleware_redirect',
                'anonymous',
                'unknown',
                ip_address,
                False,
                f"Unauthenticated user redirected to login from {request.path}"
            )
            return redirect('login')

        # Проверяем, требуется ли группа EISGS_Users для данного URL
        if self._requires_users_group(request.path) and not request.session.get('in_users', False):
            ip_address = self._get_client_ip(request)
            user_info = request.session.get('user_info', {})
            username = user_info.get('username', 'unknown')
            log_auth_event(
                'middleware_access_denied',
                username,
                'unknown',
                ip_address,
                False,
                f"User {username} denied access to {request.path} - not in EISGS_Users group"
            )
            return redirect('home')

        response = self.get_response(request)
        return response

    def _requires_auth(self, path):
        """Проверяет, требует ли URL авторизации"""
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                return False
        return True

    def _requires_users_group(self, path):
        """Проверяет, требует ли URL группу EISGS_Users"""
        for users_url in self.users_required_urls:
            if path.startswith(users_url):
                return True
        return False

    def _is_authenticated(self, request):
        """Проверяет, авторизован ли пользователь"""
        ip_address = self._get_client_ip(request)
        
        # Проверяем наличие токенов в сессии
        access_token = request.session.get('access')
        refresh_token = request.session.get('refresh')
        
        if not access_token:
            log_auth_event(
                'middleware_no_token',
                'anonymous',
                'unknown',
                ip_address,
                False,
                "No access token in session"
            )
            return False

        # Проверяем валидность access_token
        if self._check_token_valid(access_token):
            # Получаем информацию о пользователе
            user_info = self._get_user_info(access_token)
            if user_info:
                # Нормализация и сохранение ранее известного имени/домена
                prev_user_info = request.session.get('user_info', {}) or {}
                if not user_info.get('username') or str(user_info.get('username')).strip() == 'None':
                    user_info['username'] = prev_user_info.get('username') or 'user'
                if not user_info.get('domain'):
                    user_info['domain'] = prev_user_info.get('domain') or 'belstat'
                request.session['user_info'] = user_info
                log_auth_event(
                    'middleware_token_valid',
                    user_info.get('username', 'unknown'),
                    'unknown',
                    ip_address,
                    True,
                    None
                )
                return True
            else:
                log_auth_event(
                    'middleware_user_info_failed',
                    'unknown',
                    'unknown',
                    ip_address,
                    False,
                    "Failed to get user info"
                )
                return False
        else:
            # Токен истек, пытаемся обновить
            log_auth_event(
                'middleware_token_expired',
                'unknown',
                'unknown',
                ip_address,
                False,
                "Access token expired, attempting refresh"
            )
            new_access_token = self._refresh_token(refresh_token)
            if new_access_token:
                request.session['access'] = new_access_token
                user_info = self._get_user_info(new_access_token)
                if user_info:
                    prev_user_info = request.session.get('user_info', {}) or {}
                    if not user_info.get('username') or str(user_info.get('username')).strip() == 'None':
                        user_info['username'] = prev_user_info.get('username') or 'user'
                    if not user_info.get('domain'):
                        user_info['domain'] = prev_user_info.get('domain') or 'belstat'
                    request.session['user_info'] = user_info
                    log_auth_event(
                        'middleware_token_refreshed',
                        user_info.get('username', 'unknown'),
                        'unknown',
                        ip_address,
                        True,
                        None
                    )
                    return True
            
            # Не удалось обновить токен, очищаем сессию
            log_auth_event(
                'middleware_refresh_failed',
                'unknown',
                'unknown',
                ip_address,
                False,
                "Failed to refresh token, clearing session"
            )
            request.session.flush()
            return False

    def _check_token_valid(self, access_token):
        """Проверяет валидность access_token"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.auth_api_base}/check_token',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Token validation successful")
                return True
            else:
                logger.debug(f"Token validation failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking token validity: {e}")
            return False

    def _refresh_token(self, refresh_token):
        """Обновляет access_token используя refresh_token"""
        try:
            headers = {
                'Authorization': f'Bearer {refresh_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.auth_api_base}/refresh_token',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('token')
                if new_token:
                    logger.info("Token refreshed successfully")
                    return new_token
                else:
                    logger.error("No token in refresh response")
                    return None
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing refresh response: {e}")
            return None

    def _get_user_info(self, access_token):
        """Получает информацию о пользователе"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.auth_api_base}/get_data"
            masked_headers = headers.copy()
            if masked_headers.get('Authorization'):
                masked_headers['Authorization'] = f"Bearer {access_token}"
            logger.info(f"GET_DATA request → url={url}, headers={masked_headers}, timeout=10")
            
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )
            
            try:
                response_headers = dict(response.headers)
            except Exception:
                response_headers = {}
            logger.info(f"GET_DATA response ← status={response.status_code}, headers={response_headers}")
            logger.info(f"GET_DATA body ← {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                user_section = data.get('user') or {}
                username_value = None
                try:
                    username_value = user_section.get('username')
                except AttributeError:
                    username_value = None
                if not username_value:
                    username_value = data.get('username')
                guid_raw = (user_section.get('guid') if isinstance(user_section, dict) else None) or data.get('guid')
                guid_value = str(guid_raw).strip('{}') if guid_raw else None
                domain_value = user_section.get('domain') if isinstance(user_section, dict) else data.get('domain')
                
                user_info = {
                    'guid': guid_value,
                    'username': username_value,
                    'domain': domain_value
                }
                logger.debug(f"User info retrieved: {user_info['username']}")
                return user_info
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user info: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing user info response: {e}")
            return None

    def _get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
