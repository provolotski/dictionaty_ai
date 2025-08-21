#!/usr/bin/env python3
"""
Скрипт для обновления данных пользователей из API аутентификации
Обновляет поля department и is_user на основе данных из Active Directory
"""

import requests
import json
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_users.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UserDataUpdater:
    def __init__(self, auth_api_url: str, backend_api_url: str):
        self.auth_api_url = auth_api_url.rstrip('/')
        self.backend_api_url = backend_api_url.rstrip('/')
        
    def get_user_groups(self, access_token: str) -> List[str]:
        """Получение групп пользователя из API аутентификации"""
        try:
            url = f"{self.auth_api_url}/api/v1/auth/domain/user/groups"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'groups' in data:
                    return data['groups']
                else:
                    logger.warning(f"Неожиданный формат ответа для групп: {data}")
                    return []
            else:
                logger.error(f"Ошибка получения групп: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения групп пользователя: {e}")
            return []
    
    def get_user_data(self, access_token: str) -> Optional[Dict]:
        """Получение персональных данных пользователя из API аутентификации"""
        try:
            url = f"{self.auth_api_url}/api/v1/auth/get_data"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Получены данные пользователя: {data}")
                return data
            else:
                logger.error(f"Ошибка получения данных пользователя: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения данных пользователя: {e}")
            return None
    
    def get_all_users_from_backend(self) -> List[Dict]:
        """Получение всех пользователей из backend"""
        try:
            url = f"{self.backend_api_url}/api/v1/users/"
            params = {"page": 1, "page_size": 1000}  # Получаем всех пользователей
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'users' in data:
                    return data['users']
                else:
                    logger.error(f"Неожиданный формат ответа: {data}")
                    return []
            else:
                logger.error(f"Ошибка получения пользователей: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователей из backend: {e}")
            return []
    
    def update_user_in_backend(self, user_id: int, user_data: Dict) -> bool:
        """Обновление пользователя в backend"""
        try:
            url = f"{self.backend_api_url}/api/v1/users/{user_id}"
            
            # Подготавливаем данные для обновления
            update_data = {
                "guid": user_data.get("guid", ""),
                "name": user_data.get("name", ""),
                "is_active": user_data.get("is_active", True),
                "is_admin": user_data.get("is_admin", False),
                "department": user_data.get("department"),
                "is_user": user_data.get("is_user", False)
            }
            
            response = requests.put(url, json=update_data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Пользователь {user_id} успешно обновлен")
                return True
            else:
                logger.error(f"Ошибка обновления пользователя {user_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
            return False
    
    def process_user_update(self, user: Dict, access_token: str) -> bool:
        """Обработка обновления одного пользователя"""
        try:
            user_id = user.get('id')
            guid = user.get('guid', '').strip('{}')
            
            if not user_id or not guid:
                logger.warning(f"Пропускаем пользователя с неполными данными: {user}")
                return False
            
            logger.info(f"Обработка пользователя {user_id} ({guid})")
            
            # Получаем актуальные данные из API аутентификации
            user_auth_data = self.get_user_data(access_token)
            if not user_auth_data:
                logger.warning(f"Не удалось получить данные для пользователя {user_id}")
                return False
            
            # Получаем группы пользователя
            user_groups = self.get_user_groups(access_token)
            
            # Определяем флаги на основе групп
            is_user = 'EISGS_Users' in user_groups
            is_admin = user.get('is_admin', False)  # Сохраняем существующий флаг
            
            # Получаем подразделение из атрибута OU (если есть)
            department = user_auth_data.get('ou') or user_auth_data.get('department')
            
            # Подготавливаем данные для обновления
            update_data = {
                "id": user_id,
                "guid": guid,
                "name": user_auth_data.get('username', user.get('name', '')),
                "is_active": user.get('is_active', True),
                "is_admin": is_admin,
                "department": department,
                "is_user": is_user
            }
            
            # Обновляем пользователя в backend
            success = self.update_user_in_backend(user_id, update_data)
            
            if success:
                logger.info(f"Пользователь {user_id} обновлен: department='{department}', is_user={is_user}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка обработки пользователя {user.get('id', 'unknown')}: {e}")
            return False
    
    def run_update(self, access_token: str):
        """Основной метод для запуска обновления"""
        try:
            logger.info("Начинаем обновление данных пользователей...")
            
            # Получаем всех пользователей из backend
            users = self.get_all_users_from_backend()
            
            if not users:
                logger.warning("Не найдено пользователей для обновления")
                return
            
            logger.info(f"Найдено {len(users)} пользователей для обновления")
            
            # Обрабатываем каждого пользователя
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    if self.process_user_update(user, access_token):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Критическая ошибка при обработке пользователя {user.get('id')}: {e}")
                    error_count += 1
            
            logger.info(f"Обновление завершено. Успешно: {success_count}, Ошибок: {error_count}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обновлении: {e}")


def main():
    """Основная функция"""
    # Настройки (можно вынести в конфигурационный файл)
    AUTH_API_URL = os.getenv('AUTH_API_URL', 'http://127.0.0.1:9090')
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:8000')
    
    # Токен доступа (в реальном использовании должен получаться из системы аутентификации)
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    
    if not ACCESS_TOKEN:
        logger.error("Не указан ACCESS_TOKEN. Установите переменную окружения ACCESS_TOKEN")
        return
    
    # Создаем экземпляр обновления и запускаем процесс
    updater = UserDataUpdater(AUTH_API_URL, BACKEND_API_URL)
    updater.run_update(ACCESS_TOKEN)


if __name__ == "__main__":
    main()
