"""
Модуль для управления владельцами справочников
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas import DictionaryOwnerIn, DictionaryOwnerOut, DictionaryOwnerWithInfo
from database import database

logger = logging.getLogger(__name__)


class DictionaryOwnerService:
    """
    Сервис для управления владельцами справочников
    """

    @staticmethod
    async def create_ownership(dictionary_id: int, user_id: int) -> Optional[DictionaryOwnerOut]:
        """
        Создание записи о владении справочником
        
        Args:
            dictionary_id: ID справочника
            user_id: ID пользователя
            
        Returns:
            DictionaryOwnerOut или None в случае ошибки
        """
        try:
            # Проверяем, что справочник и пользователь существуют
            dict_check = await database.fetch_one(
                "SELECT id FROM dictionary WHERE id = :dict_id",
                {"dict_id": dictionary_id}
            )
            
            user_check = await database.fetch_one(
                "SELECT id FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )
            
            if not dict_check:
                logger.error(f"Справочник с ID {dictionary_id} не найден")
                return None
                
            if not user_check:
                logger.error(f"Пользователь с ID {user_id} не найден")
                return None
            
            # Создаем запись о владении
            query = """
                INSERT INTO dictionary_owner (id_dictionary, id_user, created_at, updated_at)
                VALUES (:dict_id, :user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, id_dictionary, id_user, created_at, updated_at
            """
            
            result = await database.fetch_one(
                query,
                {"dict_id": dictionary_id, "user_id": user_id}
            )
            
            if result:
                logger.info(f"Создана запись о владении: справочник {dictionary_id}, пользователь {user_id}")
                return DictionaryOwnerOut(**result)
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания записи о владении: {e}")
            return None

    @staticmethod
    async def delete_ownership(dictionary_id: int, user_id: int) -> bool:
        """
        Удаление записи о владении справочником
        
        Args:
            dictionary_id: ID справочника
            user_id: ID пользователя
            
        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            query = """
                DELETE FROM dictionary_owner 
                WHERE id_dictionary = :dict_id AND id_user = :user_id
            """
            
            result = await database.execute(
                query,
                {"dict_id": dictionary_id, "user_id": user_id}
            )
            
            if result:
                logger.info(f"Удалена запись о владении: справочник {dictionary_id}, пользователь {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления записи о владении: {e}")
            return False

    @staticmethod
    async def get_user_ownership(user_id: int) -> List[DictionaryOwnerWithInfo]:
        """
        Получение списка справочников, которыми владеет пользователь
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список справочников с информацией
        """
        try:
            # Сначала получаем базовые записи владения
            ownership_query = """
                SELECT 
                    do.id,
                    do.id_dictionary,
                    do.id_user,
                    do.created_at,
                    do.updated_at
                FROM dictionary_owner do
                WHERE do.id_user = :user_id
                ORDER BY do.id_dictionary
            """
            
            ownership_rows = await database.fetch_all(ownership_query, {"user_id": user_id})
            logger.debug(f"Найдено {len(ownership_rows)} записей владения для пользователя {user_id}")
            
            if not ownership_rows:
                return []
            
            # Получаем информацию о справочниках и пользователе
            result = []
            for row in ownership_rows:
                try:
                    # Получаем информацию о справочнике
                    dict_query = "SELECT code, name FROM dictionary WHERE id = :dict_id"
                    dict_row = await database.fetch_one(dict_query, {"dict_id": row["id_dictionary"]})
                    
                    # Получаем информацию о пользователе
                    user_query = "SELECT name FROM users WHERE id = :user_id"
                    user_row = await database.fetch_one(user_query, {"user_id": row["id_user"]})
                    
                    if dict_row and user_row:
                        result.append(DictionaryOwnerWithInfo(
                            id=row["id"],
                            id_dictionary=row["id_dictionary"],
                            dictionary_code=dict_row["code"] or "",
                            dictionary_name=dict_row["name"] or f"Справочник #{row['id_dictionary']}",
                            id_user=row["id_user"],
                            user_name=user_row["name"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"]
                        ))
                    else:
                        logger.warning(f"Не найдены данные для словаря {row['id_dictionary']} или пользователя {row['id_user']}")
                except Exception as inner_e:
                    logger.error(f"Ошибка обработки записи владения {row['id']}: {inner_e}")
                    continue
            
            logger.info(f"Получено {len(result)} справочников для пользователя {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения справочников пользователя {user_id}: {e}")
            return []

    @staticmethod
    async def get_dictionary_owners(dictionary_id: int) -> List[DictionaryOwnerWithInfo]:
        """
        Получение списка владельцев справочника
        
        Args:
            dictionary_id: ID справочника
            
        Returns:
            Список владельцев с информацией
        """
        try:
            query = """
                SELECT 
                    do.id,
                    do.id_dictionary,
                    d.code as dictionary_code,
                    d.name as dictionary_name,
                    do.id_user,
                    u.name as user_name,
                    do.created_at,
                    do.updated_at
                FROM dictionary_owner do
                JOIN dictionary d ON do.id_dictionary = d.id
                JOIN users u ON do.id_user = u.id
                WHERE do.id_dictionary = :dict_id
                ORDER BY u.name
            """
            
            rows = await database.fetch_all(query, {"dict_id": dictionary_id})
            
            result = [DictionaryOwnerWithInfo(**row) for row in rows]
            logger.debug(f"Получено {len(result)} владельцев для справочника {dictionary_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения владельцев справочника {dictionary_id}: {e}")
            return []

    @staticmethod
    async def check_ownership(dictionary_id: int, user_id: int) -> bool:
        """
        Проверка, является ли пользователь владельцем справочника
        
        Args:
            dictionary_id: ID справочника
            user_id: ID пользователя
            
        Returns:
            True если пользователь является владельцем
        """
        try:
            query = """
                SELECT id FROM dictionary_owner 
                WHERE id_dictionary = :dict_id AND id_user = :user_id
            """
            
            result = await database.fetch_one(
                query,
                {"dict_id": dictionary_id, "user_id": user_id}
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Ошибка проверки владения: {e}")
            return False

    @staticmethod
    async def get_all_dictionaries() -> List[Dict[str, Any]]:
        """
        Получение списка всех справочников для выбора
        
        Returns:
            Список справочников с кодом и названием
        """
        try:
            query = """
                SELECT id, code, name 
                FROM dictionary 
                WHERE id_status = 1  -- Только действующие справочники
                ORDER BY name
            """
            
            rows = await database.fetch_all(query)
            
            result = [
                {
                    "id": row["id"],
                    "code": row["code"],
                    "name": row["name"]
                }
                for row in rows
            ]
            
            logger.debug(f"Получено {len(result)} справочников для выбора")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения списка справочников: {e}")
            return []
