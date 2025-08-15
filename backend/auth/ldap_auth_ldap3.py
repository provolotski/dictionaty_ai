"""
Аутентификация через Active Directory с использованием ldap3
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ldap3 import Server, Connection, ALL, SUBTREE, LEVEL, NTLM, SIMPLE, ANONYMOUS
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPInvalidCredentialsError

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема безопасности для JWT токенов
security = HTTPBearer()


class LDAPAuthenticator:
    """Аутентификатор через Active Directory с использованием ldap3"""
    
    def __init__(self):
        self.ldap_server = settings.ldap_server
        self.domain = settings.ldap_domain
        self.base_dn = settings.ldap_base_dn
        self.bind_dn = settings.ldap_bind_dn
        self.bind_password = settings.ldap_bind_password
        self.user_search_base = settings.ldap_user_search_base
        self.group_search_base = settings.ldap_group_search_base
        self.required_group = settings.ldap_required_group
        self.use_ssl = settings.ldap_use_ssl
        self.use_tls = settings.ldap_use_tls
        self.timeout = settings.ldap_timeout
        
        # Создание сервера
        self.server = Server(
            self.ldap_server.replace('ldap://', '').replace('ldaps://', ''),
            use_ssl=self.use_ssl,
            get_info=ALL,
            connect_timeout=self.timeout
        )
    
    def _get_ldap_connection(self, user_dn: str = None, password: str = None) -> Connection:
        """Создание соединения с LDAP"""
        try:
            # Определяем метод аутентификации
            if user_dn and password:
                # Аутентификация пользователя
                conn = Connection(
                    self.server,
                    user=user_dn,
                    password=password,
                    authentication=SIMPLE,
                    auto_bind=True,
                    receive_timeout=self.timeout
                )
            elif self.bind_dn and self.bind_password:
                # Привязка с сервисным аккаунтом
                conn = Connection(
                    self.server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    authentication=SIMPLE,
                    auto_bind=True,
                    receive_timeout=self.timeout
                )
            else:
                # Анонимная привязка
                conn = Connection(
                    self.server,
                    authentication=ANONYMOUS,
                    auto_bind=True,
                    receive_timeout=self.timeout
                )
            
            # Настройка TLS
            if self.use_tls and not self.use_ssl:
                conn.start_tls()
            
            return conn
            
        except LDAPBindError as e:
            logger.error(f"Ошибка привязки к LDAP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка конфигурации аутентификации"
            )
        except LDAPException as e:
            logger.error(f"Ошибка подключения к LDAP: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервер аутентификации недоступен"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка подключения к LDAP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка подключения к серверу аутентификации"
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Аутентификация пользователя через Active Directory
        
        Args:
            username: Имя пользователя
            password: Пароль пользователя
            
        Returns:
            Dict с информацией о пользователе или None
        """
        try:
            # Поиск пользователя
            user_dn = self._find_user_dn(username)
            if not user_dn:
                logger.warning(f"Пользователь {username} не найден в AD")
                return None
            
            # Проверка пароля
            try:
                conn = self._get_ldap_connection(user_dn, password)
                conn.unbind()
            except LDAPInvalidCredentialsError:
                logger.warning(f"Неверный пароль для пользователя {username}")
                return None
            
            # Получение информации о пользователе
            user_info = self._get_user_info(user_dn)
            if not user_info:
                logger.warning(f"Не удалось получить информацию о пользователе {username}")
                return None
            
            # Проверка членства в группе
            if not self._is_user_in_group(user_dn, self.required_group):
                logger.warning(f"Пользователь {username} не состоит в группе {self.required_group}")
                return None
            
            # Получение групп пользователя
            user_groups = self._get_user_groups(user_dn)
            
            user_data = {
                "username": username,
                "display_name": user_info.get("displayName", [""])[0],
                "email": user_info.get("mail", [""])[0],
                "dn": user_dn,
                "groups": user_groups,
                "department": user_info.get("department", [""])[0],
                "title": user_info.get("title", [""])[0],
                "employee_id": user_info.get("employeeID", [""])[0],
                "last_login": datetime.now().isoformat()
            }
            
            logger.info(f"Успешная аутентификация пользователя {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации пользователя {username}: {e}")
            return None
    
    def _find_user_dn(self, username: str) -> Optional[str]:
        """Поиск DN пользователя"""
        try:
            conn = self._get_ldap_connection()
            
            # Поиск по sAMAccountName
            filter_str = f"(&(objectClass=user)(sAMAccountName={username}))"
            attrs = ["distinguishedName"]
            
            conn.search(
                search_base=self.user_search_base,
                search_filter=filter_str,
                search_scope=SUBTREE,
                attributes=attrs
            )
            
            if conn.entries:
                user_dn = conn.entries[0].entry_dn
                conn.unbind()
                return user_dn
            
            conn.unbind()
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска пользователя {username}: {e}")
            return None
    
    def _get_user_info(self, user_dn: str) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            conn = self._get_ldap_connection()
            
            attrs = [
                "displayName", "mail", "department", "title", 
                "employeeID", "memberOf", "sAMAccountName"
            ]
            
            conn.search(
                search_base=user_dn,
                search_filter="(objectClass=user)",
                search_scope=LEVEL,
                attributes=attrs
            )
            
            if conn.entries:
                user_info = {}
                entry = conn.entries[0]
                for attr in attrs:
                    if hasattr(entry, attr):
                        user_info[attr] = getattr(entry, attr).values
                    else:
                        user_info[attr] = [""]
                
                conn.unbind()
                return user_info
            
            conn.unbind()
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_dn}: {e}")
            return None
    
    def _is_user_in_group(self, user_dn: str, group_name: str) -> bool:
        """Проверка членства пользователя в группе"""
        try:
            conn = self._get_ldap_connection()
            
            # Поиск группы
            filter_str = f"(&(objectClass=group)(sAMAccountName={group_name}))"
            attrs = ["distinguishedName", "member"]
            
            conn.search(
                search_base=self.group_search_base,
                search_filter=filter_str,
                search_scope=SUBTREE,
                attributes=attrs
            )
            
            if not conn.entries:
                logger.warning(f"Группа {group_name} не найдена")
                conn.unbind()
                return False
            
            group_dn = conn.entries[0].entry_dn
            members = getattr(conn.entries[0], 'member', [])
            
            # Проверка прямого членства
            if user_dn in members:
                conn.unbind()
                return True
            
            # Проверка вложенного членства (рекурсивно)
            result = self._check_nested_membership(user_dn, group_dn)
            conn.unbind()
            return result
            
        except Exception as e:
            logger.error(f"Ошибка проверки членства в группе {group_name}: {e}")
            return False
    
    def _check_nested_membership(self, user_dn: str, group_dn: str, visited: set = None) -> bool:
        """Рекурсивная проверка вложенного членства в группе"""
        if visited is None:
            visited = set()
        
        if group_dn in visited:
            return False  # Избегаем циклических ссылок
        
        visited.add(group_dn)
        
        try:
            # Получение групп, в которых состоит пользователь
            user_groups = self._get_user_groups(user_dn)
            
            for group in user_groups:
                if group == group_dn:
                    return True
                
                # Рекурсивная проверка
                if self._check_nested_membership(group, group_dn, visited):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки вложенного членства: {e}")
            return False
    
    def _get_user_groups(self, user_dn: str) -> List[str]:
        """Получение списка групп пользователя"""
        try:
            conn = self._get_ldap_connection()
            
            attrs = ["memberOf"]
            
            conn.search(
                search_base=user_dn,
                search_filter="(objectClass=user)",
                search_scope=LEVEL,
                attributes=attrs
            )
            
            if conn.entries:
                member_of = getattr(conn.entries[0], 'memberOf', [])
                groups = [str(group) for group in member_of]
                conn.unbind()
                return groups
            
            conn.unbind()
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения групп пользователя {user_dn}: {e}")
            return []


class JWTHandler:
    """Обработчик JWT токенов"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def create_access_token(self, data: dict) -> str:
        """Создание access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Создание refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка refresh token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None


class AuthService:
    """Сервис аутентификации"""
    
    def __init__(self):
        self.ldap_auth = LDAPAuthenticator()
        self.jwt_handler = JWTHandler()
    
    async def authenticate_and_create_tokens(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Аутентификация пользователя и создание токенов
        
        Args:
            username: Имя пользователя
            password: Пароль пользователя
            
        Returns:
            Dict с токенами и информацией о пользователе или None
        """
        try:
            # Аутентификация через LDAP
            user_data = self.ldap_auth.authenticate_user(username, password)
            if not user_data:
                return None
            
            # Создание токенов
            access_token = self.jwt_handler.create_access_token(
                data={"sub": username, "user_data": user_data}
            )
            refresh_token = self.jwt_handler.create_refresh_token(
                data={"sub": username}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.jwt_handler.access_token_expire_minutes * 60,
                "user": user_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания токенов для пользователя {username}: {e}")
            return None
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Обновление токенов
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dict с новыми токенами или None
        """
        try:
            # Проверка refresh token
            payload = self.jwt_handler.verify_refresh_token(refresh_token)
            if not payload:
                return None
            
            username = payload.get("sub")
            if not username:
                return None
            
            # Получение информации о пользователе
            user_dn = self.ldap_auth._find_user_dn(username)
            if not user_dn:
                return None
            
            user_data = self.ldap_auth._get_user_info(user_dn)
            if not user_data:
                return None
            
            # Создание новых токенов
            access_token = self.jwt_handler.create_access_token(
                data={"sub": username, "user_data": user_data}
            )
            new_refresh_token = self.jwt_handler.create_refresh_token(
                data={"sub": username}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": self.jwt_handler.access_token_expire_minutes * 60,
                "user": user_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка обновления токенов: {e}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Получение текущего пользователя по токену
        
        Args:
            token: Access token
            
        Returns:
            Dict с информацией о пользователе или None
        """
        try:
            payload = self.jwt_handler.verify_token(token)
            if not payload:
                return None
            
            return payload.get("user_data")
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по токену: {e}")
            return None


# Глобальные экземпляры
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
    """
    Получение текущего пользователя из токена
    
    Args:
        credentials: HTTP авторизационные данные
        
    Returns:
        Dict с информацией о пользователе
        
    Raises:
        HTTPException: Если токен недействителен
    """
    try:
        token = credentials.credentials
        user_data = await auth_service.get_current_user(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения текущего пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_group(group_name: str = settings.ldap_required_group):
    """
    Декоратор для проверки членства в группе
    
    Args:
        group_name: Название требуемой группы
        
    Returns:
        Функция-декоратор
    """
    async def check_group_membership(user: Dict[str, Any] = get_current_user) -> Dict[str, Any]:
        """
        Проверка членства пользователя в группе
        
        Args:
            user: Информация о пользователе
            
        Returns:
            Информация о пользователе
            
        Raises:
            HTTPException: Если пользователь не состоит в группе
        """
        user_groups = user.get("groups", [])
        
        if group_name not in user_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется членство в группе: {group_name}"
            )
        
        return user
    
    return check_group_membership
