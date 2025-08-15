"""
Аутентификация через Active Directory
"""

import ldap
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема безопасности для JWT токенов
security = HTTPBearer()


class LDAPAuthenticator:
    """Аутентификатор через Active Directory"""
    
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
        
        # Настройка LDAP
        ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, self.timeout)
        ldap.set_option(ldap.OPT_TIMEOUT, self.timeout)
        
        if self.use_tls:
            ldap.set_option(ldap.OPT_TLS_REQUIRE_CERT, ldap.OPT_TLS_NEVER)
    
    def _get_ldap_connection(self) -> ldap.ldapobject.LDAPObject:
        """Создание соединения с LDAP"""
        try:
            if self.use_ssl:
                conn = ldap.initialize(f"ldaps://{self.ldap_server.replace('ldap://', '')}")
            else:
                conn = ldap.initialize(self.ldap_server)
            
            # Настройка TLS
            if self.use_tls and not self.use_ssl:
                conn.start_tls_s()
            
            # Привязка с сервисным аккаунтом (если указан)
            if self.bind_dn and self.bind_password:
                conn.simple_bind_s(self.bind_dn, self.bind_password)
            else:
                # Анонимная привязка
                conn.simple_bind_s()
            
            return conn
            
        except ldap.SERVER_DOWN:
            logger.error("LDAP сервер недоступен")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервер аутентификации недоступен"
            )
        except ldap.INVALID_CREDENTIALS:
            logger.error("Неверные учетные данные для привязки к LDAP")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка конфигурации аутентификации"
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к LDAP: {e}")
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
            conn = self._get_ldap_connection()
            
            # Поиск пользователя
            user_dn = self._find_user_dn(conn, username)
            if not user_dn:
                logger.warning(f"Пользователь {username} не найден в AD")
                return None
            
            # Проверка пароля
            try:
                conn.simple_bind_s(user_dn, password)
            except ldap.INVALID_CREDENTIALS:
                logger.warning(f"Неверный пароль для пользователя {username}")
                return None
            
            # Получение информации о пользователе
            user_info = self._get_user_info(conn, user_dn)
            if not user_info:
                logger.warning(f"Не удалось получить информацию о пользователе {username}")
                return None
            
            # Проверка членства в группе
            if not self._is_user_in_group(conn, user_dn, self.required_group):
                logger.warning(f"Пользователь {username} не состоит в группе {self.required_group}")
                return None
            
            # Получение групп пользователя
            user_groups = self._get_user_groups(conn, user_dn)
            
            user_data = {
                "username": username,
                "display_name": user_info.get("displayName", [b""])[0].decode("utf-8"),
                "email": user_info.get("mail", [b""])[0].decode("utf-8"),
                "dn": user_dn,
                "groups": user_groups,
                "department": user_info.get("department", [b""])[0].decode("utf-8"),
                "title": user_info.get("title", [b""])[0].decode("utf-8"),
                "employee_id": user_info.get("employeeID", [b""])[0].decode("utf-8"),
                "last_login": datetime.now().isoformat()
            }
            
            logger.info(f"Успешная аутентификация пользователя {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации пользователя {username}: {e}")
            return None
        finally:
            try:
                conn.unbind_s()
            except:
                pass
    
    def _find_user_dn(self, conn: ldap.ldapobject.LDAPObject, username: str) -> Optional[str]:
        """Поиск DN пользователя"""
        try:
            # Поиск по sAMAccountName
            filter_str = f"(&(objectClass=user)(sAMAccountName={username}))"
            attrs = ["distinguishedName"]
            
            result = conn.search_s(
                self.user_search_base,
                ldap.SCOPE_SUBTREE,
                filter_str,
                attrs
            )
            
            if result and len(result) > 0:
                return result[0][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска пользователя {username}: {e}")
            return None
    
    def _get_user_info(self, conn: ldap.ldapobject.LDAPObject, user_dn: str) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            attrs = [
                "displayName", "mail", "department", "title", 
                "employeeID", "memberOf", "sAMAccountName"
            ]
            
            result = conn.search_s(
                user_dn,
                ldap.SCOPE_BASE,
                "(objectClass=user)",
                attrs
            )
            
            if result and len(result) > 0:
                return result[0][1]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_dn}: {e}")
            return None
    
    def _is_user_in_group(self, conn: ldap.ldapobject.LDAPObject, user_dn: str, group_name: str) -> bool:
        """Проверка членства пользователя в группе"""
        try:
            # Поиск группы
            filter_str = f"(&(objectClass=group)(sAMAccountName={group_name}))"
            attrs = ["distinguishedName", "member"]
            
            result = conn.search_s(
                self.group_search_base,
                ldap.SCOPE_SUBTREE,
                filter_str,
                attrs
            )
            
            if not result or len(result) == 0:
                logger.warning(f"Группа {group_name} не найдена")
                return False
            
            group_dn = result[0][0]
            members = result[0][1].get("member", [])
            
            # Проверка прямого членства
            if user_dn.encode() in members:
                return True
            
            # Проверка вложенного членства (рекурсивно)
            return self._check_nested_membership(conn, user_dn, group_dn)
            
        except Exception as e:
            logger.error(f"Ошибка проверки членства в группе {group_name}: {e}")
            return False
    
    def _check_nested_membership(self, conn: ldap.ldapobject.LDAPObject, user_dn: str, group_dn: str, visited: set = None) -> bool:
        """Рекурсивная проверка вложенного членства в группе"""
        if visited is None:
            visited = set()
        
        if group_dn in visited:
            return False  # Избегаем циклических ссылок
        
        visited.add(group_dn)
        
        try:
            # Получение групп, в которых состоит пользователь
            user_groups = self._get_user_groups(conn, user_dn)
            
            for group in user_groups:
                if group == group_dn:
                    return True
                
                # Рекурсивная проверка
                if self._check_nested_membership(conn, group, group_dn, visited):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки вложенного членства: {e}")
            return False
    
    def _get_user_groups(self, conn: ldap.ldapobject.LDAPObject, user_dn: str) -> List[str]:
        """Получение списка групп пользователя"""
        try:
            attrs = ["memberOf"]
            
            result = conn.search_s(
                user_dn,
                ldap.SCOPE_BASE,
                "(objectClass=user)",
                attrs
            )
            
            if result and len(result) > 0:
                member_of = result[0][1].get("memberOf", [])
                return [group.decode("utf-8") for group in member_of]
            
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
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка refresh token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                return None
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
            Dict с токенами и информацией о пользователе
        """
        # Аутентификация через LDAP
        user_data = self.ldap_auth.authenticate_user(username, password)
        if not user_data:
            return None
        
        # Создание токенов
        token_data = {
            "sub": username,
            "display_name": user_data["display_name"],
            "email": user_data["email"],
            "groups": user_data["groups"],
            "department": user_data["department"],
            "title": user_data["title"],
            "employee_id": user_data["employee_id"]
        }
        
        access_token = self.jwt_handler.create_access_token(token_data)
        refresh_token = self.jwt_handler.create_refresh_token({"sub": username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_handler.access_token_expire_minutes * 60,
            "user": user_data
        }
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Обновление токенов
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dict с новыми токенами
        """
        payload = self.jwt_handler.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        username = payload.get("sub")
        if not username:
            return None
        
        # Получение актуальной информации о пользователе
        # В реальном приложении здесь можно добавить кэширование
        token_data = {
            "sub": username,
            "display_name": payload.get("display_name", ""),
            "email": payload.get("email", ""),
            "groups": payload.get("groups", []),
            "department": payload.get("department", ""),
            "title": payload.get("title", ""),
            "employee_id": payload.get("employee_id", "")
        }
        
        access_token = self.jwt_handler.create_access_token(token_data)
        new_refresh_token = self.jwt_handler.create_refresh_token({"sub": username})
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_handler.access_token_expire_minutes * 60
        }
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Получение текущего пользователя по токену
        
        Args:
            token: JWT токен
            
        Returns:
            Dict с информацией о пользователе
        """
        payload = self.jwt_handler.verify_token(token)
        if not payload:
            return None
        
        return {
            "username": payload.get("sub"),
            "display_name": payload.get("display_name"),
            "email": payload.get("email"),
            "groups": payload.get("groups", []),
            "department": payload.get("department"),
            "title": payload.get("title"),
            "employee_id": payload.get("employee_id")
        }


# Глобальный экземпляр сервиса аутентификации
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
    """
    Зависимость для получения текущего пользователя
    
    Args:
        credentials: HTTP заголовки авторизации
        
    Returns:
        Dict с информацией о пользователе
        
    Raises:
        HTTPException: Если токен недействителен
    """
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def require_group(group_name: str = settings.ldap_required_group):
    """
    Зависимость для проверки членства в группе
    
    Args:
        group_name: Название группы
        
    Returns:
        Функция-зависимость
    """
    async def check_group_membership(user: Dict[str, Any] = get_current_user) -> Dict[str, Any]:
        if group_name not in [group.split(",")[0].replace("CN=", "") for group in user.get("groups", [])]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется членство в группе {group_name}"
            )
        return user
    
    return check_group_membership
