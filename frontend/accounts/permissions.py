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
    SECURITY_GROUPS = ['EISGS_AppSecurity', 'Администраторы безопасности ЦИТ']  # Альтернативные названия для админов безопасности
    USER_GROUPS = ['EISGS_Users']  # Группы пользователей
    
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
            groups, department = self._get_user_groups(username, domain, access_token)
            
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
            
            # Сохраняем информацию о группах в базе данных
            self._save_user_groups(username, domain, groups, user_guid)
            
            # Сохраняем подразделение в сессии
            if hasattr(request, 'session') and department:
                request.session['user_department'] = department
                logger.debug(f"Подразделение сохранено в сессии: {department}")
                
                # Также обновляем подразделение в базе данных
                if self._update_user_department_in_db(username, domain, department, user_guid):
                    logger.info(f"Подразделение {department} сохранено в базе данных для пользователя {username}@{domain}")
                else:
                    logger.warning(f"Не удалось сохранить подразделение {department} в базе данных для пользователя {username}@{domain}")
            
            # Проверяем, есть ли у пользователя необходимые группы
            # Проверяем наличие группы безопасности (админ) или пользователей
            has_security_access = any(group in self.SECURITY_GROUPS for group in groups)
            has_user_access = any(group in self.USER_GROUPS for group in groups)
            has_access = has_security_access or has_user_access
            
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
                'user_guid': user_guid,
                'department': department,
                'has_security_access': has_security_access,
                'has_user_access': has_user_access,
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
    
    def _get_user_department_from_api(self, access_token):
        """
        Получает подразделение пользователя из API, если не удается извлечь из групп
        """
        try:
            url = f"{self.base_url}/get_data"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            if resp.status_code != 200:
                logger.debug(f"get_data для подразделения status={resp.status_code} body={resp.text}")
                return None
            data = resp.json()
            
            # Ищем подразделение в различных полях
            department = None
            user_section = data.get('user') or {}
            
            # Проверяем различные возможные поля
            for field in ['department', 'ou', 'organization', 'division']:
                if field in user_section and user_section[field]:
                    department = user_section[field]
                    logger.debug(f"Найдено подразделение в поле {field}: {department}")
                    break
                elif field in data and data[field]:
                    department = data[field]
                    logger.debug(f"Найдено подразделение в корневом поле {field}: {department}")
                    break
            
            return department
        except Exception as e:
            logger.debug(f"_get_user_department_from_api error: {e}")
            return None

    def _update_user_department_in_db(self, username, domain, department, guid=None):
        """
        Обновляет подразделение пользователя в базе данных
        """
        try:
            from django.conf import settings
            import requests
            
            # Используем правильный API endpoint для users
            backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
            # Заменяем /api/v2 на /api/v1 для users endpoints
            url = backend_api_url.replace('/api/v2', '/api/v1') + "/users/update-department"
            
            # Данные для обновления
            update_data = {
                "username": username,
                "domain": domain,
                "department": department
            }
            
            if guid:
                update_data["guid"] = guid
            
            logger.info(f"Обновление подразделения пользователя: {url}, данные: {update_data}")
            
            # Отправляем PATCH запрос для обновления
            response = requests.patch(url, json=update_data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Подразделение пользователя {username}@{domain} обновлено: {department}")
                return True
            else:
                logger.error(f"Ошибка обновления подразделения: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка обновления подразделения пользователя {username}@{domain}: {e}")
            return False

    def _extract_department_from_groups(self, groups_data):
        """
        Извлекает подразделение пользователя из OU атрибута групп
        """
        try:
            logger.debug(f"Извлечение подразделения из групп: {groups_data}")
            
            for group in groups_data:
                if isinstance(group, dict) and 'dn' in group:
                    dn = group['dn']
                    logger.debug(f"Обрабатываем DN: {dn}")
                    
                    # Ищем OU= в DN
                    if 'OU=' in dn:
                        # Извлекаем все OU значения
                        ou_parts = []
                        dn_parts = dn.split(',')
                        for part in dn_parts:
                            part = part.strip()
                            if part.startswith('OU='):
                                ou_value = part[3:]  # Убираем 'OU='
                                logger.debug(f"Найден OU: {ou_value}")
                                
                                # Фильтруем стандартные OU
                                if ou_value and ou_value not in ['Builtin', 'Users', 'Domain Users', 'Builtin', 'Users', 'Domain Users']:
                                    ou_parts.append(ou_value)
                        
                        logger.debug(f"Найденные OU части: {ou_parts}")
                        
                        if ou_parts:
                            # Приоритет: сначала ищем OU с "ЦИТ" или "Белстата"
                            for ou in ou_parts:
                                if 'ЦИТ' in ou or 'Белстата' in ou:
                                    logger.debug(f"Найдено приоритетное подразделение: {ou}")
                                    return ou
                            
                            # Если не нашли приоритетное, возвращаем первое
                            logger.debug(f"Возвращаем первое подразделение: {ou_parts[0]}")
                            return ou_parts[0]
            
            logger.debug("Подразделение не найдено")
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении подразделения из групп: {e}")
            return None

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
                    
                    # Извлекаем подразделение из групп
                    department = self._extract_department_from_groups(raw_groups)
                    logger.debug(f"Извлеченное подразделение из групп: {department}")
                    
                    # Если не удалось получить подразделение из групп, пробуем из API
                    if not department:
                        department = self._get_user_department_from_api(access_token)
                        logger.debug(f"Подразделение из API: {department}")
                    
                    # Если все способы не дали результата, используем домен как fallback
                    if not department:
                        department = domain.upper()
                        logger.debug(f"Используем домен как подразделение: {department}")
                    
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
                    
                    # Возвращаем кортеж (группы, подразделение)
                    return groups, department
                elif response.status_code in (401, 403):
                    logger.warning(f"Проверка групп вернула {response.status_code} для {username}@{domain}")
                    logger.debug(f"Ответ сервера: {response.text}")
                    return [], None
                else:
                    logger.warning(f"API вернул статус {response.status_code} для {username}@{domain}")
                    logger.debug(f"Ответ сервера: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка запроса к API (попытка {attempt + 1}): {e}")
                if attempt == self.retries - 1:
                    raise
        return [], None

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
            
            # Обновляем поле is_user в backend на основе принадлежности к группе EISGS_Users
            self._update_is_user_field(username, domain, groups, guid)
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении групп для {username}@{domain}: {e}")
    
    def _update_is_user_field(self, username, domain, groups, guid=None):
        """
        Обновляет поле is_user в backend на основе принадлежности к группе EISGS_Users
        """
        try:
            # Проверяем, входит ли пользователь в группу EISGS_Users
            is_user = 'EISGS_Users' in groups
            
            logger.debug(f"Обновление поля is_user для {username}@{domain}: {is_user} (группы: {groups})")
            
            # Если есть GUID, используем endpoint обновления по GUID
            if guid:
                from django.conf import settings
                import requests
                
                backend_api_url = getattr(settings, 'BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
                url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/guid/{guid}"
                
                # Получаем текущие данные пользователя
                try:
                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        user_data = response.json()
                        
                        # Обновляем только поле is_user, если оно изменилось
                        if user_data.get('is_user') != is_user:
                            # Подготавливаем данные для обновления
                            update_data = {
                                "guid": user_data.get("guid"),
                                "name": user_data.get("name"),
                                "is_active": user_data.get("is_active", True),
                                "is_admin": user_data.get("is_admin", False),
                                "department": user_data.get("department"),
                                "is_user": is_user
                            }
                            
                            # Отправляем PUT запрос для обновления
                            put_url = backend_api_url.replace('/api/v2', '/api/v1') + f"/users/{user_data['id']}"
                            put_response = requests.put(put_url, json=update_data, timeout=15)
                            
                            if put_response.status_code == 200:
                                logger.info(f"Поле is_user обновлено для {username}@{domain}: {is_user}")
                            else:
                                logger.warning(f"Ошибка обновления is_user: {put_response.status_code} - {put_response.text}")
                        else:
                            logger.debug(f"Поле is_user уже актуально для {username}@{domain}: {is_user}")
                    else:
                        logger.warning(f"Не удалось получить данные пользователя для обновления is_user: {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.warning(f"Ошибка при обновлении is_user для {username}@{domain}: {e}")
            else:
                logger.debug(f"GUID не найден для {username}@{domain}, пропускаем обновление is_user")
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении is_user для {username}@{domain}: {e}")
    
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
