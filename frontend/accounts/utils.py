import logging
from requests.exceptions import RequestException
import requests
from django.conf import settings
# from urllib3 import request
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def api_get(request, path, service='dict'):
    access = request.session.get('access')
    # refresh= request.session.get('refresh')
    headers = {'Authorization': f'Bearer  {access}'} if access else {}

    base_url = settings.API_DICT['BASE_URL'] if service == 'dict' else settings.API_OATH['BASE_URL']
    url = f"{base_url}{path}"
    responce = requests.get(url, headers=headers)

    if (responce.status_code == 401 and request.session.get('refresh')):
        logger.debug('trying to refresh token')
        refresh_response = requests.post(f'{settings.API_OATH["BASE_URL"]}/refresh_token',json={"refresh":request.session.get('refresh')})

    # if refresh_response.status_code == 200:
    #     new_access_token = refresh_response.json().get('access_token')
    #     request.session['access'] = new_access_token
    #     headers['Authorization'] = f'Bearer {new_access_token}'
    #     responce = requests.get(url, headers=headers)
    return responce

def api_post(path, data=None, service='auth'):
    """Отправка POST запроса к API"""
    logger.debug(f'Отправка POST запроса к {service} API: {path}')
    
    # Используем новую конфигурацию авторизации
    if service == 'auth':
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        if auth_config.get('USE_EXTERNAL_API', True) and auth_config.get('EXTERNAL_API', {}).get('ENABLED', True):
            base_url = auth_config['EXTERNAL_API']['BASE_URL']
        else:
            # Fallback на старую конфигурацию
            base_url = settings.API_OATH['BASE_URL']
    else:
        base_url = settings.API_DICT['BASE_URL']
    
    url = f"{base_url}{path}"
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    
    try:
        # Проверяем тип данных
        if hasattr(data, 'model_dump_json'):
            # Если это Pydantic модель
            json_data = data.model_dump_json()
            logger.debug(f"Используем Pydantic модель: {type(data).__name__}")
        else:
            # Если это обычный словарь или другой объект
            json_data = data
            logger.debug(f"Используем обычные данные: {type(data).__name__}, содержимое: {data}")
            
        logger.debug(f"Отправляем данные: {json_data}")
        
        # Получаем таймаут из конфигурации
        timeout = 30
        if service == 'auth':
            auth_config = getattr(settings, 'AUTH_CONFIG', {})
            timeout = auth_config.get('EXTERNAL_API', {}).get('TIMEOUT', 30)
        
        response = requests.post(
            url,
            json=json_data,
            headers=headers,
            timeout=timeout
        )
        
        logger.debug(f'Ответ от API: {response.status_code}')
        return response
        
    except RequestException as e:
        logger.error(f"API Error ({url}): {str(e)}")
        return None


def api_post_create_dict(path:str, data):
    logger.debug(f'Отправка запроса на создание справочника: {path}')
    base_url = settings.API_DICT['BASE_URL']
    url = f"{base_url}{path}"
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    try:
        # Проверяем тип данных
        if hasattr(data, 'model_dump'):
            # Если это Pydantic модель, используем model_dump() для получения словаря
            json_data = data.model_dump()
            logger.debug(f"Используем Pydantic модель: {type(data).__name__}")
        elif hasattr(data, 'model_dump_json'):
            # Если это Pydantic модель с model_dump_json
            json_data = data.model_dump()
            logger.debug(f"Используем Pydantic модель (model_dump_json): {type(data).__name__}")
        else:
            # Если это обычный словарь или другой объект
            json_data = data
            logger.debug(f"Используем обычные данные: {type(data).__name__}")
        
        logger.debug(f"Отправляем данные: {json_data}")
        
        response = requests.post(
            url,
            json=json_data,
            headers=headers,
            timeout=30
        )
        
        logger.debug(f'Ответ от API: {response.status_code}')
        return response
        
    except RequestException as e:
        logger.error(f"API Error ({url}): {str(e)}")
        return None



def api_post_dict(path, data=None, service='auth'):    
    base_url = settings.AUTH_CONFIG['EXTERNAL_API']['BASE_URL'] if service == 'auth' else settings.API_DICT['BASE_URL']
    url = f"{base_url}{path}"
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=30
        )
        if response is not None:  # Явная проверка
            logger.debug(response.status_code)
            return response
        return None, "API не вернул ответ"
    except RequestException as e:
        logger.error(f"API Error ({url}): {str(e)}")
        return None


def log_user_action(action: str, details: Dict[str, Any], user_info: Optional[Dict] = None, 
                   ip_address: Optional[str] = None, success: bool = True):
    """
    Логирует действия пользователя с автоматическим добавлением даты и времени
    
    Args:
        action: Описание действия
        details: Детали действия
        user_info: Информация о пользователе
        ip_address: IP адрес пользователя
        success: Успешность действия
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'action': action,
        'success': success,
        'details': details
    }
    
    if user_info:
        log_data['user'] = user_info
    if ip_address:
        log_data['ip_address'] = ip_address
    
    if success:
        logger.info(f"USER_ACTION: {action} - {details}")
    else:
        logger.warning(f"USER_ACTION_FAILED: {action} - {details}")
    
    return log_data

def log_auth_event(event_type: str, username: str, domain: str = None, 
                  ip_address: str = None, success: bool = True, 
                  error_message: str = None):
    """
    Логирует события авторизации с автоматическим добавлением даты и времени
    
    Args:
        event_type: Тип события (login, logout, token_refresh, etc.)
        username: Имя пользователя
        domain: Домен пользователя
        ip_address: IP адрес
        success: Успешность события
        error_message: Сообщение об ошибке
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'event_type': event_type,
        'username': username,
        'domain': domain,
        'ip_address': ip_address,
        'success': success
    }
    
    if error_message:
        log_data['error'] = error_message
    
    if success:
        logger.info(f"AUTH_EVENT: {event_type} - User: {username}@{domain} - IP: {ip_address}")
    else:
        logger.warning(f"AUTH_EVENT_FAILED: {event_type} - User: {username}@{domain} - IP: {ip_address} - Error: {error_message}")
    
    return log_data

def log_system_event(event_type: str, message: str, level: str = 'INFO', 
                    additional_data: Dict[str, Any] = None):
    """
    Логирует системные события с автоматическим добавлением даты и времени
    
    Args:
        event_type: Тип системного события
        message: Сообщение
        level: Уровень логирования
        additional_data: Дополнительные данные
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'event_type': event_type,
        'message': message,
        'level': level
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    log_message = f"SYSTEM_EVENT: {event_type} - {message}"
    if additional_data:
        log_message += f" - Data: {additional_data}"
    
    if level.upper() == 'DEBUG':
        logger.debug(log_message)
    elif level.upper() == 'INFO':
        logger.info(log_message)
    elif level.upper() == 'WARNING':
        logger.warning(log_message)
    elif level.upper() == 'ERROR':
        logger.error(log_message)
    elif level.upper() == 'CRITICAL':
        logger.critical(log_message)
    else:
        logger.info(log_message)
    
    return log_data


def post_login_audit_to_backend(username: str, domain: str, ip_address: str, user_agent: str,
                                action: str, status: str, comment: str, guid: str = None) -> None:
    """
    Отправляет запись аудита неуспешного логина на backend эндпоинт /api/v1/audit/log.
    Не бросает исключений наружу, ошибки только логируются.
    """
    try:
        base_v2 = settings.API_DICT.get('BASE_URL', 'http://127.0.0.1:8000/api/v2')
        # Переключаемся на v1 на том же хосте
        if base_v2.endswith('/api/v2'):
            base_v1 = base_v2[:-len('/api/v2')] + '/api/v1'
        else:
            base_v1 = base_v2.replace('/api/v2/', '/api/v1/').replace('/api/v2', '/api/v1')
            if '/api/v1' not in base_v1:
                base_v1 = base_v1.rstrip('/') + '/api/v1'
        url = f"{base_v1}/audit/log"

        payload = {
            "username": username or "",
            "domain": domain or "",
            "ip_address": ip_address or "",
            "user_agent": user_agent or "",
            "action": action or "login_failed",
            "status": status or "failed",
            "comment": comment or ""
        }
        if guid:
            try:
                payload["guid"] = str(guid).strip('{}')
            except Exception:
                pass
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        logger.info(f"AUDIT POST → {url} payload={payload}")
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info(f"AUDIT POST ← status={resp.status_code} body={resp.text}")
    except Exception as e:
        logger.warning(f"Не удалось отправить аудит неуспешного логина: {e}")


def _backend_base_v1() -> str:
    base_v2 = settings.API_DICT.get('BASE_URL', 'http://127.0.0.1:8000/api/v2')
    if base_v2.endswith('/api/v2'):
        return base_v2[:-len('/api/v2')] + '/api/v1'
    base_v1 = base_v2.replace('/api/v2/', '/api/v1/').replace('/api/v2', '/api/v1')
    if '/api/v1' not in base_v1:
        base_v1 = base_v1.rstrip('/') + '/api/v1'
    return base_v1


def fetch_audit_logs_from_backend(params: Dict[str, Any]) -> Optional[list]:
    """
    Запрашивает список логов аудита с backend эндпоинта /api/v1/audit/logs
    params: словарь query-параметров (date_from, date_to, status, action, username, limit, offset)
    """
    try:
        base_v1 = _backend_base_v1()
        url = f"{base_v1}/audit/logs"
        logger.info(f"AUDIT GET → {url} params={params}")
        resp = requests.get(url, params=params, timeout=15)
        logger.info(f"AUDIT GET ← status={resp.status_code}")
        if resp.status_code != 200:
            logger.warning(f"Ошибка получения логов аудита: {resp.text}")
            return None
        data = resp.json()
        if isinstance(data, list):
            return data
        return None
    except Exception as e:
        logger.warning(f"Не удалось получить логи аудита: {e}")
        return None


def fetch_users_from_backend(params: Dict[str, Any]) -> Optional[dict]:
    """
    Запрашивает список пользователей с backend эндпоинта /api/v1/users/
    params: словарь query-параметров (domain, search, page, page_size)
    """
    try:
        base_v1 = _backend_base_v1()
        url = f"{base_v1}/users"
        logger.info(f"USERS GET → {url} params={params}")
        resp = requests.get(url, params=params, timeout=15)
        logger.info(f"USERS GET ← status={resp.status_code}")
        if resp.status_code != 200:
            logger.warning(f"Ошибка получения пользователей: {resp.text}")
            return None
        data = resp.json()
        if isinstance(data, dict) and 'users' in data:
            return data
        return None
    except Exception as e:
        logger.warning(f"Не удалось получить пользователей: {e}")
        return None


def update_user_in_backend(user_id: int, user_data: Dict[str, Any]) -> Optional[dict]:
    """
    Обновляет информацию о пользователе через backend эндпоинт PUT /api/v1/users/{user_id}
    user_id: ID пользователя для обновления
    user_data: словарь с данными для обновления (name, is_admin)
    """
    try:
        base_v1 = _backend_base_v1()
        
        # Сначала получаем существующего пользователя
        get_url = f"{base_v1}/users/{user_id}"
        logger.info(f"USERS GET → {get_url}")
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        get_resp = requests.get(get_url, headers=headers, timeout=15)
        
        if get_resp.status_code != 200:
            logger.warning(f"Ошибка получения пользователя для обновления: {get_resp.text}")
            return None
            
        existing_user = get_resp.json()
        logger.info(f"USERS GET ← status={get_resp.status_code}")
        
        # Создаем полную модель для обновления, объединяя существующие данные с новыми
        full_user_data = {
            "guid": existing_user.get("guid"),
            "name": existing_user.get("name"),
            "is_active": existing_user.get("is_active", True),
            "is_admin": existing_user.get("is_admin", False),
            "department": existing_user.get("department"),
            "is_user": existing_user.get("is_user", False)
        }
        
        # Обновляем только переданные поля
        full_user_data.update(user_data)
        
        # Отправляем PUT запрос с полными данными
        put_url = f"{base_v1}/users/{user_id}"
        logger.info(f"USERS PUT → {put_url} data={full_user_data}")
        
        put_resp = requests.put(put_url, json=full_user_data, headers=headers, timeout=15)
        
        logger.info(f"USERS PUT ← status={put_resp.status_code}")
        if put_resp.status_code != 200:
            logger.warning(f"Ошибка обновления пользователя: {put_resp.text}")
            return None
            
        data = put_resp.json()
        if isinstance(data, dict) and 'id' in data:
            return data
        return None
    except Exception as e:
        logger.warning(f"Не удалось обновить пользователя: {e}")
        return None


def create_or_update_user_in_backend(username, domain, department, guid, is_user=False):
    """Создание или обновление пользователя в backend с подразделением и группой"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + "/users/upsert"
        
        data = {
            "username": username,
            "domain": domain,
            "department": department,
            "guid": guid,
            "is_user": is_user,
            "is_active": True,
            "is_admin": False
        }
        
        logger.info(f"Создание/обновление пользователя: {url}, данные: {data}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Пользователь {username}@{domain} создан/обновлен в backend")
            return result
        else:
            logger.error(f"Ошибка создания/обновления пользователя: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка создания/обновления пользователя {username}@{domain}: {e}")
        return None


def update_user_last_login(guid):
    """Обновляет время последнего входа пользователя по GUID"""
    try:
        from django.conf import settings
        
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        
        # Получаем пользователя по GUID
        get_url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/guid/{guid}"
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        get_resp = requests.get(get_url, headers=headers, timeout=15)
        
        if get_resp.status_code != 200:
            logger.warning(f"Не удалось найти пользователя с GUID {guid} для обновления last_login")
            return False
            
        user_data = get_resp.json()
        user_id = user_data.get('id')
        
        if not user_id:
            logger.warning(f"Не найден ID пользователя с GUID {guid}")
            return False
        
        # Обновляем пользователя с новым временем входа
        full_user_data = {
            "guid": user_data.get("guid"),
            "name": user_data.get("name"),
            "is_active": user_data.get("is_active", True),
            "is_admin": user_data.get("is_admin", False),
            "department": user_data.get("department"),
            "is_user": user_data.get("is_user", False)
        }
        
        put_url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}"
        put_resp = requests.put(put_url, json=full_user_data, headers=headers, timeout=15)
        
        if put_resp.status_code == 200:
            logger.info(f"Время последнего входа обновлено для пользователя с GUID {guid}")
            return True
        else:
            logger.warning(f"Ошибка обновления времени входа: {put_resp.status_code} - {put_resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка обновления времени последнего входа для GUID {guid}: {e}")
        return False

def fetch_user_by_guid_from_backend(guid):
    """Получение данных пользователя по GUID из backend API"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/guid/{guid}"
        
        logger.info(f"Запрос данных пользователя по GUID: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получены данные пользователя по GUID: {guid}")
            return data
        else:
            logger.error(f"Ошибка получения данных пользователя по GUID: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя по GUID {guid}: {e}")
        return None

def update_user_department_in_backend(username, domain, department, guid=None):
    """Обновление подразделения пользователя через backend API"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + "/users/update-department"
        
        data = {
            "username": username,
            "domain": domain,
            "department": department
        }
        
        if guid:
            data["guid"] = guid
        
        logger.info(f"Обновление подразделения пользователя: {url}, данные: {data}")
        
        response = requests.patch(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Подразделение пользователя {username}@{domain} обновлено: {department}")
            return result
        else:
            logger.error(f"Ошибка обновления подразделения: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка обновления подразделения пользователя {username}@{domain}: {e}")
        return None

def fetch_user_from_backend(user_id):
    """Получение данных пользователя по ID"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}"
        
        logger.info(f"Запрос данных пользователя: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получены данные пользователя: {user_id}")
            return data
        else:
            logger.error(f"Ошибка получения данных пользователя: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя {user_id}: {e}")
        return None


def fetch_user_with_ownership_from_backend(user_id):
    """Получение данных пользователя с информацией о владении справочниками"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}/with-ownership"
        
        logger.info(f"Запрос данных пользователя с владением: {url}")
        logger.info(f"Исходный BACKEND_API_URL: {backend_api_url}")
        logger.info(f"Итоговый URL: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получены данные пользователя с владением: {user_id}")
            return data
        else:
            logger.error(f"Ошибка получения данных пользователя: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя с владением {user_id}: {e}")
        return None


def fetch_available_dictionaries_from_backend():
    """Получение списка доступных справочников для назначения владельцев"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + "/users/dictionaries/available"
        
        logger.info(f"Запрос доступных справочников: {url}")
        logger.info(f"Исходный BACKEND_API_URL: {backend_api_url}")
        logger.info(f"Итоговый URL: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получено {len(data)} доступных справочников")
            return data
        else:
            logger.error(f"Ошибка получения справочников: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения доступных справочников: {e}")
        return None


def add_dictionary_ownership_to_backend(user_id, dictionary_id):
    """Добавление права владения справочником для пользователя"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}/dictionary-ownership"
        
        data = {"id_dictionary": dictionary_id, "id_user": user_id}
        
        logger.info(f"Добавление права владения: {url}, данные: {data}")
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Право владения добавлено для пользователя {user_id}, справочник {dictionary_id}")
            return True
        else:
            logger.error(f"Ошибка добавления права владения: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка добавления права владения для пользователя {user_id}: {e}")
        return False


def remove_dictionary_ownership_from_backend(user_id, dictionary_id):
    """Удаление права владения справочником для пользователя"""
    try:
        from django.conf import settings
        
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}/dictionary-ownership/{dictionary_id}"
        
        logger.info(f"Удаление права владения: {url}")
        
        response = requests.delete(url, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Право владения удалено для пользователя {user_id}, справочник {dictionary_id}")
            return True
        else:
            logger.error(f"Ошибка удаления права владения: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка удаления права владения для пользователя {user_id}: {e}")
        return False

