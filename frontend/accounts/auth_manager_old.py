import logging
import requests
import time
from django.conf import settings
from django.contrib.auth.models import User
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class AuthManager:
    """Менеджер авторизации с поддержкой внешнего API и локальной авторизации"""
    
    def __init__(self):
        self.auth_config = getattr(settings, 'AUTH_CONFIG', {})
        self.external_api_enabled = self.auth_config.get('USE_EXTERNAL_API', True)
        self.external_api_config = self.auth_config.get('EXTERNAL_API', {})
        self.local_auth_config = self.auth_config.get('LOCAL_AUTH', {})
    
    def authenticate_user(self, username: str, password: str, domain: str = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Аутентификация пользователя через внешний API
        
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (success, token_data, error_message)
        """
        logger.info(f"=== AUTH_MANAGER: Начало аутентификации ===")
        logger.info(f"Пользователь: {username}")
        logger.info(f"Домен: {domain}")
        logger.info(f"Внешний API включен: {self.external_api_enabled}")
        logger.info(f"Внешний API настроен: {self.external_api_config.get('ENABLED', False)}")
        
        # Только внешний API
        if self.external_api_enabled and self.external_api_config.get('ENABLED', True):
            logger.info("=== Попытка аутентификации через внешний API ===")
            success, token_data, error = self._authenticate_external(username, password, domain)
            
            if success:
                logger.info(f"✅ Успешная аутентификация через внешний API для пользователя {username}")
                return True, token_data, None
            
            logger.error(f"❌ Ошибка внешнего API: {error}")
            return False, None, error
        else:
            error_msg = "Внешний API отключен"
            logger.error(f"❌ {error_msg}")
            logger.error(f"external_api_enabled: {self.external_api_enabled}")
            logger.error(f"external_api_config: {self.external_api_config}")
            return False, None, error_msg
    
    def _authenticate_external(self, username: str, password: str, domain: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Аутентификация через внешний API"""
        logger.info(f"=== ВНЕШНИЙ API: Начало ===")
        
        try:
            base_url = self.external_api_config.get('BASE_URL')
            timeout = self.external_api_config.get('TIMEOUT', 30)
            retry_attempts = self.external_api_config.get('RETRY_ATTEMPTS', 3)
            
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Timeout: {timeout} сек")
            logger.info(f"Попытки повтора: {retry_attempts}")
            
            url = f"{base_url}/login"
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            data = {
                'username': username,
                'password': password,
                'domain': domain or 'belstat'
            }
            
            logger.info(f"URL запроса: {url}")
            logger.info(f"Заголовки: {headers}")
            logger.info(f"Данные запроса: {username}@{domain}")
            logger.info(f"Полные данные (без пароля): {{'username': '{username}', 'domain': '{domain}'}}")
            
            # Попытки повторного запроса
            for attempt in range(retry_attempts):
                logger.info(f"--- Попытка {attempt + 1}/{retry_attempts} ---")
                
                try:
                    logger.info(f"Отправка POST запроса на {url}")
                    start_time = time.time()
                    
                    response = requests.post(
                        url,
                        json=data,
                        headers=headers,
                        timeout=timeout
                    )
                    
                    response_time = time.time() - start_time
                    logger.info(f"Получен ответ за {response_time:.2f} сек")
                    logger.info(f"HTTP статус: {response.status_code}")
                    logger.info(f"Заголовки ответа: {dict(response.headers)}")
                    
                    if response.content:
                        logger.info(f"Размер ответа: {len(response.content)} байт")
                        try:
                            response_json = response.json()
                            logger.info(f"JSON ответ: {response_json}")
                        except:
                            logger.info(f"Текстовый ответ: {response.text[:500]}")
                    else:
                        logger.warning("Ответ пустой")
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        if self._validate_token_response(token_data):
                            logger.info("✅ Валидный ответ с токенами получен")
                            return True, token_data, None
                        else:
                            logger.error("❌ Неверный формат ответа от внешнего API")
                            logger.error(f"Полученные данные: {token_data}")
                            return False, None, "Неверный формат ответа от внешнего API"
                    
                    elif response.status_code in [400, 401, 403]:
                        # Ошибки аутентификации
                        logger.warning(f"Ошибка аутентификации: {response.status_code}")
                        error_data = response.json() if response.content else {}
                        error_message = self._extract_error_message(error_data)
                        logger.warning(f"Извлеченное сообщение об ошибке: {error_message}")
                        return False, None, error_message
                    
                    elif response.status_code >= 500:
                        # Серверные ошибки - пробуем повторить
                        logger.error(f"Серверная ошибка: {response.status_code}")
                        if attempt < retry_attempts - 1:
                            logger.warning(f"Повторная попытка {attempt + 2} через 1 сек...")
                            time.sleep(1)
                            continue
                        else:
                            logger.error(f"Все попытки исчерпаны, серверная ошибка: {response.status_code}")
                            return False, None, f"Серверная ошибка: {response.status_code}"
                    
                    else:
                        logger.error(f"Неожиданный статус ответа: {response.status_code}")
                        return False, None, f"Неожиданный статус ответа: {response.status_code}"
                        
                except Timeout as e:
                    logger.error(f"Таймаут соединения: {e}")
                    if attempt < retry_attempts - 1:
                        logger.warning(f"Повторная попытка {attempt + 2}...")
                        continue
                    else:
                        logger.error("Все попытки исчерпаны, таймаут")
                        return False, None, "Таймаут соединения с внешним API"
                        
                except ConnectionError as e:
                    logger.error(f"Ошибка соединения: {e}")
                    if attempt < retry_attempts - 1:
                        logger.warning(f"Повторная попытка {attempt + 2}...")
                        continue
                    else:
                        logger.error("Все попытки исчерпаны, ошибка соединения")
                        return False, None, "Ошибка соединения с внешним API"
                        
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при запросе: {e}")
                    if attempt < retry_attempts - 1:
                        logger.warning(f"Повторная попытка {attempt + 2}...")
                        continue
                    else:
                        logger.error("Все попытки исчерпаны, неожиданная ошибка")
                        return False, None, f"Ошибка запроса: {str(e)}"
                        
        except Exception as e:
            logger.error(f"=== КРИТИЧЕСКАЯ ОШИБКА ВНЕШНЕГО API ===")
            logger.error(f"Тип исключения: {type(e).__name__}")
            logger.error(f"Сообщение: {str(e)}")
            logger.error("Traceback:", exc_info=True)
            return False, None, f"Ошибка внешнего API: {str(e)}"
        
        logger.error("Не удалось получить ответ от внешнего API после всех попыток")
        return False, None, "Не удалось получить ответ от внешнего API"
    
    def _authenticate_local(self, username: str, password: str, domain: str = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Локальная аутентификация через Django"""
        logger.info(f"=== ЛОКАЛЬНАЯ АВТОРИЗАЦИЯ: Начало ===")
        logger.info(f"Пользователь: {username}")
        logger.info(f"Домен: {domain}")
        
        try:
            logger.info("Поиск пользователя в локальной базе данных...")
            
            # Проверяем, существует ли пользователь
            try:
                user = User.objects.get(username=username)
                logger.info(f"✅ Пользователь найден: ID={user.id}, email={user.email}")
                logger.info(f"Активен: {user.is_active}, Стафф: {user.is_staff}, Суперпользователь: {user.is_superuser}")
            except User.DoesNotExist:
                logger.warning(f"❌ Пользователь {username} не найден в локальной базе")
                logger.info("Проверяем всех пользователей в базе...")
                all_users = User.objects.all()
                logger.info(f"Всего пользователей в базе: {all_users.count()}")
                if all_users.exists():
                    usernames = [u.username for u in all_users[:5]]  # Показываем первые 5
                    logger.info(f"Примеры пользователей: {usernames}")
                return False, None, "Пользователь не найден"
            
            # Проверяем пароль
            logger.info("Проверка пароля...")
            if user.check_password(password):
                logger.info(f"✅ Пароль верный для пользователя {username}")
                
                # Создаем mock токены для совместимости
                token_data = {
                    'access_token': f'local_token_{user.id}_{username}',
                    'refresh_token': f'local_refresh_{user.id}_{username}',
                    'user_info': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser
                    }
                }
                
                logger.info(f"Созданы mock токены: access={bool(token_data['access_token'])}, refresh={bool(token_data['refresh_token'])}")
                logger.info("=== ЛОКАЛЬНАЯ АВТОРИЗАЦИЯ: УСПЕХ ===")
                return True, token_data, None
            else:
                logger.warning(f"❌ Неверный пароль для пользователя {username}")
                return False, None, "Неверный пароль"
                
        except Exception as e:
            logger.error(f"=== ОШИБКА ЛОКАЛЬНОЙ АВТОРИЗАЦИИ ===")
            logger.error(f"Тип исключения: {type(e).__name__}")
            logger.error(f"Сообщение: {str(e)}")
            logger.error("Traceback:", exc_info=True)
            return False, None, f"Ошибка локальной аутентификации: {str(e)}"
    
    def _validate_token_response(self, token_data: Dict) -> bool:
        """Проверка корректности ответа с токенами"""
        if not isinstance(token_data, dict):
            return False
        
        required_fields = ['access_token', 'refresh_token']
        return all(field in token_data and token_data[field] for field in required_fields)
    
    def _extract_error_message(self, error_data: Dict) -> str:
        """Извлечение сообщения об ошибке из ответа API"""
        if not isinstance(error_data, dict):
            return "Неверные учетные данные"
        
        # Приоритет полей для сообщений об ошибках
        error_fields = ['error', 'message', 'detail', 'description']
        
        for field in error_fields:
            if field in error_data and error_data[field]:
                return str(error_data[field])
        
        return "Неверные учетные данные"
    
    def is_external_api_available(self) -> bool:
        """Проверка доступности внешнего API"""
        if not self.external_api_enabled or not self.external_api_config.get('ENABLED', True):
            return False
        
        try:
            base_url = self.external_api_config.get('BASE_URL')
            timeout = self.external_api_config.get('TIMEOUT', 30)
            
            # Пробуем endpoint /login с тестовыми данными
            test_data = {
                'username': 'test_user',
                'password': 'test_password',
                'domain': 'test_domain'
            }
            
            response = requests.post(
                f"{base_url}/login",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            
            # API считается доступным, если отвечает (даже с ошибкой 400/401/403)
            return response.status_code in [200, 400, 401, 403, 422]
        except:
            return False


# Создаем глобальный экземпляр
auth_manager = AuthManager()
