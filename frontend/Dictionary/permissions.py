import logging
from typing import Dict, Any, Optional
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

def can_edit_dictionary(request, dictionary_id: int) -> Dict[str, Any]:
    """
    Проверяет, может ли текущий пользователь редактировать справочник
    
    Args:
        request: Django request объект
        dictionary_id: ID справочника для проверки
        
    Returns:
        Dict с ключами:
        - can_edit: bool - может ли редактировать
        - reason: str - причина (если не может)
        - user_info: dict - информация о пользователе
        - is_admin: bool - является ли администратором
        - is_owner: bool - является ли владельцем справочника
    """
    try:
        # Получаем информацию о пользователе из сессии
        user_info = request.session.get('user_info', {})
        if not user_info:
            return {
                'can_edit': False,
                'reason': 'Пользователь не авторизован',
                'user_info': {},
                'is_admin': False,
                'is_owner': False
            }
        
        guid = user_info.get('guid')
        username = user_info.get('username')
        
        if not guid and not username:
            return {
                'can_edit': False,
                'reason': 'Недостаточно информации о пользователе',
                'user_info': user_info,
                'is_admin': False,
                'is_owner': False
            }
        
        # Проверяем, является ли пользователь администратором
        is_admin = check_if_admin(guid, username)
        
        # Если администратор - может редактировать любой справочник
        if is_admin:
            return {
                'can_edit': True,
                'reason': 'Пользователь является администратором системы',
                'user_info': user_info,
                'is_admin': True,
                'is_owner': False
            }
        
        # Проверяем, является ли пользователь владельцем справочника
        is_owner = check_if_dictionary_owner(guid, username, dictionary_id)
        
        if is_owner:
            return {
                'can_edit': True,
                'reason': 'Пользователь является владельцем справочника',
                'user_info': user_info,
                'is_admin': False,
                'is_owner': True
            }
        
        # Если не администратор и не владелец - не может редактировать
        return {
            'can_edit': False,
            'reason': 'Пользователь не является администратором или владельцем справочника',
            'user_info': user_info,
            'is_admin': False,
            'is_owner': False
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке прав на редактирование справочника: {e}")
        return {
            'can_edit': False,
            'reason': f'Ошибка проверки прав: {str(e)}',
            'user_info': request.session.get('user_info', {}),
            'is_admin': False,
            'is_owner': False
        }

def check_if_admin(guid: Optional[str], username: Optional[str]) -> bool:
    """
    Проверяет, является ли пользователь администратором системы
    
    Args:
        guid: GUID пользователя
        username: Имя пользователя
        
    Returns:
        bool: True если пользователь является администратором
    """
    try:
        # Сначала пробуем по GUID
        if guid:
            user_data = fetch_user_by_guid_from_backend(guid)
            if user_data and user_data.get('is_admin'):
                logger.info(f"Пользователь {guid} является администратором (проверка по GUID)")
                return True
        
        # Если по GUID не получилось, пробуем по username
        if username:
            # Здесь нужно реализовать поиск пользователя по username
            # Пока что возвращаем False
            logger.debug(f"Проверка администратора по username {username} не реализована")
            
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при проверке прав администратора: {e}")
        return False

def check_if_dictionary_owner(guid: Optional[str], username: Optional[str], dictionary_id: int) -> bool:
    """
    Проверяет, является ли пользователь владельцем справочника
    
    Args:
        guid: GUID пользователя
        username: Имя пользователя
        dictionary_id: ID справочника
        
    Returns:
        bool: True если пользователь является владельцем справочника
    """
    try:
        # Сначала пробуем по GUID
        if guid:
            user_data = fetch_user_by_guid_from_backend(guid)
            if user_data:
                user_id = user_data.get('id')
                if user_id:
                    # Проверяем владение справочником
                    ownership_data = fetch_user_with_ownership_from_backend(user_id)
                    if ownership_data and 'dictionary_ownership' in ownership_data:
                        owned_dictionaries = ownership_data['dictionary_ownership']
                        for owned_dict in owned_dictionaries:
                            if owned_dict.get('id_dictionary') == dictionary_id:
                                logger.info(f"Пользователь {guid} является владельцем справочника {dictionary_id}")
                                return True
        
        # Если по GUID не получилось, пробуем по username
        if username:
            # Здесь нужно реализовать поиск пользователя по username
            # Пока что возвращаем False
            logger.debug(f"Проверка владельца по username {username} не реализована")
            
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при проверке прав владельца справочника: {e}")
        return False

def fetch_user_by_guid_from_backend(guid: str) -> Optional[Dict[str, Any]]:
    """
    Получает данные пользователя по GUID из backend API
    
    Args:
        guid: GUID пользователя
        
    Returns:
        Dict с данными пользователя или None
    """
    try:
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/guid/{guid}"
        
        logger.debug(f"Запрос данных пользователя по GUID: {url}")
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Получены данные пользователя по GUID: {guid}")
            return data
        else:
            logger.warning(f"Ошибка получения данных пользователя по GUID: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя по GUID {guid}: {e}")
        return None

def fetch_user_with_ownership_from_backend(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает данные пользователя с информацией о владении справочниками
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Dict с данными пользователя и владением или None
    """
    try:
        # Используем правильный API endpoint для users
        backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
        # Заменяем /api/v2 на /api/v1 для users endpoints
        url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_id}/with-ownership"
        
        logger.debug(f"Запрос данных пользователя с владением: {url}")
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Получены данные пользователя с владением: {user_id}")
            return data
        else:
            logger.warning(f"Ошибка получения данных пользователя с владением: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя с владением {user_id}: {e}")
        return None
