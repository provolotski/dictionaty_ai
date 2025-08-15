import logging
import requests
from django.conf import settings
from .models import UserGroup, LoginAudit

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Получение IP адреса клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PermissionChecker:
    """Класс для проверки прав доступа пользователей"""
    
    REQUIRED_GROUPS = ['EISGS_AppSecurity', 'EISGS_Users']
    
    def __init__(self):
        # Используем BASE_URL из API_OATH для чтения групп
        self.base_url = settings.API_OATH.get('BASE_URL', 'http://127.0.0.1:9090/api/v1/auth')
        # Таймаут/ретраи можно оставить из AUTH_CONFIG.EXTERNAL_API либо использовать дефолты
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        external_api = auth_config.get('EXTERNAL_API', {})
        self.timeout = external_api.get('TIMEOUT', 30)
        self.retries = external_api.get('RETRY_ATTEMPTS', 3)
        logger.debug(f"PermissionChecker using BASE_URL (API_OATH): {self.base_url}")

    def check_user_permissions(self, username, domain, access_token, request=None):
        """
        Проверяет права доступа пользователя
        """
        try:
            logger.info(f"Проверка прав доступа для пользователя {username} в домене {domain}")
            logger.debug(f"PermissionChecker BASE_URL: {self.base_url}")
            
            # Получаем группы пользователя из внешнего API
            groups = self._get_user_groups(username, domain, access_token)
            
            if not groups:
                error_msg = "Не удалось получить информацию о группах пользователя"
                logger.warning(f"{error_msg} для {username}@{domain}")
                return {
                    'has_access': False,
                    'groups': [],
                    'error_message': error_msg
                }
            
            # Получаем GUID пользователя для консистентной идентификации
            user_guid = self._get_user_guid(access_token)
            logger.debug(f"Resolved user GUID for {username}@{domain}: {user_guid}")
            
            # Сохраняем информацию о группах (и по логину, и по GUID, если он известен)
            self._save_user_groups(username=username, domain=domain, groups=groups, guid=user_guid)
            
            # Проверяем, есть ли у пользователя необходимые группы
            has_access = any(group in self.REQUIRED_GROUPS for group in groups)
            
            # Логируем результат проверки
            if has_access:
                logger.info(f"Пользователь {username}@{domain} имеет доступ. Группы: {groups}")
            else:
                logger.warning(f"Пользователь {username}@{domain} не имеет доступа. Группы: {groups}")
            
            # Логируем в аудит
            if request:
                self._log_permission_check(username, domain, has_access, groups, request)
            
            return {
                'has_access': has_access,
                'groups': groups,
                'error_message': None if has_access else "У Вас недостаточно прав для входа в систему"
            }
            
        except Exception as e:
            error_msg = f"Ошибка при проверке прав доступа: {str(e)}"
            logger.error(f"{error_msg} для {username}@{domain}: {e}")
            
            return {
                'has_access': False,
                'groups': [],
                'error_message': error_msg
            }
    
    def _get_user_groups(self, username, domain, access_token):
        """
        Получает группы пользователя из внешнего API
        """
        endpoint = f"{self.base_url}/domain/user/groups"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Endpoint: {endpoint}")
        logger.debug(f"Headers: {{'Authorization': 'Bearer ***', 'Content-Type': 'application/json'}}")
        logger.debug(f"Access token (первые 50 символов): {access_token[:50] if access_token else 'None'}...")
        logger.debug(f"Access token длина: {len(access_token) if access_token else 0}")
        
        if access_token:
            access_token = access_token.strip()
            token_parts = access_token.split('.')
            logger.debug(f"Количество частей токена: {len(token_parts)}")
            if len(token_parts) != 3:
                logger.warning(f"Токен не имеет правильный JWT формат: {len(token_parts)} частей вместо 3")
        
        headers['Authorization'] = f'Bearer {access_token}'
        
        for attempt in range(self.retries):
            try:
                logger.debug(f"Попытка {attempt + 1} получения групп для {username}@{domain}")
                response = requests.get(endpoint, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Raw groups response: {data}")
                    raw_groups = data.get('groups') or data.get('data') or []
                    # Попытка найти массив внутри словаря
                    if isinstance(raw_groups, dict):
                        for v in raw_groups.values():
                            if isinstance(v, list):
                                raw_groups = v
                                break
                    groups: list[str] = []
                    if isinstance(raw_groups, list):
                        for item in raw_groups:
                            if isinstance(item, str):
                                groups.append(item)
                            elif isinstance(item, dict):
                                # поддерживаем различные поля наименование группы
                                name = None
                                for key in ['name', 'group_name', 'title', 'cn', 'sAMAccountName', 'samaccountname']:
                                    if key in item and item[key]:
                                        name = item[key]
                                        break
                                if name:
                                    groups.append(str(name))
                    logger.debug(f"Нормализованные группы: {groups}")
                    return groups
                elif response.status_code in (401, 403):
                    logger.warning(f"Проверка групп вернула {response.status_code} для {username}@{domain}")
                    logger.debug(f"Ответ сервера: {response.text}")
                    return []
                else:
                    logger.warning(f"API вернул статус {response.status_code} для {username}@{domain}")
                    logger.debug(f"Ответ сервера: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка запроса к API (попытка {attempt + 1}): {e}")
                if attempt == self.retries - 1:
                    raise
        return []

    def _get_user_guid(self, access_token: str) -> str | None:
        """Возвращает GUID пользователя по access_token через /get_data"""
        try:
            url = f"{self.base_url}/get_data"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            if resp.status_code != 200:
                logger.debug(f"get_data status={resp.status_code} body={resp.text}")
                return None
            data = resp.json()
            user_section = data.get('user') or {}
            guid = user_section.get('guid') or data.get('guid')
            if guid:
                guid = str(guid).strip('{}')
            return guid
        except Exception as e:
            logger.debug(f"_get_user_guid error: {e}")
            return None

    def _save_user_groups(self, username, domain, groups, guid: str | None = None):
        """
        Сохраняет информацию о группах пользователя в базе данных
        — записывает под логином и, при наличии, под GUID
        """
        try:
            # Чистим старые записи
            del_login = UserGroup.objects.filter(username=username, domain=domain)
            del_login_count = del_login.count()
            del_login.delete()
            del_guid_count = 0
            if guid:
                del_guid = UserGroup.objects.filter(username=guid, domain=domain)
                del_guid_count = del_guid.count()
                del_guid.delete()
            
            # Создаём новые записи под обеими идентичностями
            added_login = 0
            added_guid = 0
            for group in groups:
                UserGroup.objects.create(username=username, domain=domain, group_name=group)
                added_login += 1
                if guid:
                    UserGroup.objects.create(username=guid, domain=domain, group_name=group)
                    added_guid += 1
            
            logger.debug(
                f"Группы сохранены для {username}@{domain} (+ GUID={guid}): "
                f"удалено login={del_login_count}, guid={del_guid_count}; "
                f"добавлено login={added_login}, guid={added_guid}. Список: {groups}"
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении групп для {username}@{domain}: {e}")
    
    def _log_permission_check(self, username, domain, has_access, groups, request):
        """
        Логирует проверку прав доступа в аудит
        """
        try:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            LoginAudit.objects.create(
                username=username,
                domain=domain,
                ip_address=ip_address,
                user_agent=user_agent,
                status='success' if has_access else 'blocked',
                error_message=None if has_access else "Недостаточно прав для входа в систему",
                external_api_response={'groups': groups}
            )
            
        except Exception as e:
            logger.error(f"Ошибка при логировании проверки прав для {username}@{domain}: {e}")


def check_user_access(username, domain, access_token, request=None):
    """
    Утилитная функция для проверки прав доступа пользователя
    """
    checker = PermissionChecker()
    return checker.check_user_permissions(username, domain, access_token, request)
