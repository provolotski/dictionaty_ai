"""
Роутер для управления пользователями системы
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from databases import Database
from typing import Any, List, Optional, Dict
from datetime import datetime
import math

from database import get_database
from schemas import UserOut, UserIn, UserListResponse, DictionaryOwnerIn, DictionaryOwnerOut, DictionaryOwnerWithInfo, UserWithDictionaryOwnership
from models.model_dictionary_owner import DictionaryOwnerService
from utils.logger import setup_logger

logger = setup_logger(__name__)

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поиск по имени пользователя или подразделению"),
    department: Optional[str] = Query(None, description="Фильтр по подразделению"),
    is_user: Optional[bool] = Query(None, description="Фильтр по флагу is_user"),
    db: Database = Depends(get_database)
) -> Any:
    """
    Получение списка пользователей с пагинацией и фильтрацией
    """
    logger.debug(f"Получение списка пользователей с пагинацией и фильтрацией")
    try:
        # Базовый запрос
        base_query = """
            SELECT id, guid, name, is_active, is_admin, department, is_user, 
                   created_at, updated_at, last_login_at
            FROM users
            WHERE 1=1
        """
        
        # Параметры для фильтрации
        params = {}
        
        # Добавляем поиск
        if search:
            base_query += " AND (name ILIKE :search OR department ILIKE :search)"
            params["search"] = f"%{search}%"
        
        # Добавляем фильтр по подразделению
        if department:
            base_query += " AND department = :department"
            params["department"] = department
        
        # Добавляем фильтр по флагу is_user
        if is_user is not None:
            base_query += " AND is_user = :is_user"
            params["is_user"] = is_user
        
        # Подсчет общего количества
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
        total_count = await db.fetch_val(query=count_query, values=params)
        
        # Добавляем сортировку и пагинацию
        base_query += " ORDER BY name LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        
        # Выполняем запрос
        users = await db.fetch_all(query=base_query, values=params)
        
        # Вычисляем общее количество страниц
        total_pages = (total_count + page_size - 1) // page_size
        
        logger.info(f"USERS_LIST → page={page}, page_size={page_size}, total={total_count}")
        
        return UserListResponse(
            users=users,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: Database = Depends(get_database)) -> Any:
    """
    Получение информации о пользователе по ID
    """
    logger.debug(f"Получение информации о пользователе {user_id}")
    try:
        query = """
            SELECT id, guid, name, is_active, is_admin, department, is_user, 
                   created_at, updated_at, last_login_at
            FROM users 
            WHERE id = :user_id
        """
        
        user = await db.fetch_one(query=query, values={"user_id": user_id})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"USER_GET → user_id={user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/guid/{guid}", response_model=UserOut)
async def get_user_by_guid(guid: str, db: Database = Depends(get_database)) -> Any:
    """
    Получение информации о пользователе по GUID
    """
    logger.debug(f"Получение информации о пользователе по GUID: {guid}")
    try:
        # Нормализуем GUID (убираем фигурные скобки)
        normalized_guid = guid.strip('{}')
        
        query = """
            SELECT id, guid, name, is_active, is_admin, department, is_user, 
                   created_at, updated_at, last_login_at
            FROM users 
            WHERE guid = :guid
        """
        
        user = await db.fetch_one(query=query, values={"guid": normalized_guid})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"USER_GET_BY_GUID → guid={normalized_guid}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по GUID {guid}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.post("/upsert", response_model=UserOut)
async def upsert_user(user_data: dict, db: Database = Depends(get_database)) -> Any:
    """
    Создание или обновление пользователя (upsert)
    """
    try:
        username = user_data.get("username")
        domain = user_data.get("domain")
        department = user_data.get("department")
        guid = user_data.get("guid")
        is_user = user_data.get("is_user", False)
        is_active = user_data.get("is_active", True)
        is_admin = user_data.get("is_admin", False)
        
        if not username or not domain or not guid:
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать username, domain и guid"
            )
        
        # Нормализуем GUID (убираем фигурные скобки)
        normalized_guid = guid.strip('{}')
        
        # Проверяем, существует ли пользователь с таким GUID
        existing_user = await db.fetch_one(
            query="SELECT id FROM users WHERE guid = :guid",
            values={"guid": normalized_guid}
        )
        
        if existing_user:
            # Обновляем существующего пользователя
            query = """
                UPDATE users 
                SET name = :name, department = :department, is_user = :is_user,
                    is_active = :is_active, is_admin = :is_admin, updated_at = NOW()
                WHERE guid = :guid
                RETURNING id, guid, name, is_active, is_admin, department, is_user, 
                          created_at, updated_at, last_login_at
            """
            
            values = {
                "guid": normalized_guid,
                "name": username,
                "department": department,
                "is_user": is_user,
                "is_active": is_active,
                "is_admin": is_admin
            }
            
            updated_user = await db.fetch_one(query=query, values=values)
            logger.info(f"USER_UPDATE → user_id={updated_user['id']}, name={username}")
            return updated_user
        else:
            # Создаем нового пользователя - используем только поля, которые есть в схеме
            query = """
                INSERT INTO users (guid, name, is_active, is_admin, department, is_user, created_at, updated_at, last_login_at)
                VALUES (:guid, :name, :is_active, :is_admin, :department, :is_user, NOW(), NOW(), NOW())
                RETURNING id, guid, name, is_active, is_admin, department, is_user, 
                          created_at, updated_at, last_login_at
            """
            
            values = {
                "guid": normalized_guid,
                "name": username,
                "is_active": is_active,
                "is_admin": is_admin,
                "department": department,
                "is_user": is_user
            }
            
            new_user = await db.fetch_one(query=query, values=values)
            logger.info(f"USER_CREATE → user_id={new_user['id']}, name={username}")
            return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка upsert пользователя: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.post("/", response_model=UserOut)
async def create_user(user_data: UserIn, db: Database = Depends(get_database)) -> Any:
    """
    Создание нового пользователя
    """
    try:
        # Проверяем, что пользователь с таким GUID не существует
        existing_user = await db.fetch_one(
            query="SELECT id FROM users WHERE guid = :guid",
            values={"guid": user_data.guid}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким GUID уже существует"
            )
        
        # Создаем пользователя
        query = """
            INSERT INTO users (guid, name, is_active, is_admin, department, is_user)
            VALUES (:guid, :name, :is_active, :is_admin, :department, :is_user)
            RETURNING id, guid, name, is_active, is_admin, department, is_user, 
                      created_at, updated_at, last_login_at
        """
        
        values = {
            "guid": user_data.guid,
            "name": user_data.name,
            "is_active": user_data.is_active,
            "is_admin": user_data.is_admin,
            "department": user_data.department,
            "is_user": user_data.is_user
        }
        
        new_user = await db.fetch_one(query=query, values=values)
        
        logger.info(f"USER_CREATE → user_id={new_user['id']}, name={user_data.name}")
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, 
    user_data: UserIn, 
    db: Database = Depends(get_database)
) -> Any:
    """
    Обновление информации о пользователе
    """
    try:
        # Проверяем существование пользователя
        existing_user = await db.fetch_one(
            query="SELECT id, guid FROM users WHERE id = :user_id",
            values={"user_id": user_id}
        )
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Проверяем уникальность GUID (если изменился)
        if user_data.guid != existing_user["guid"]:
            guid_exists = await db.fetch_one(
                query="SELECT id FROM users WHERE guid = :guid AND id != :user_id",
                values={"guid": user_data.guid, "user_id": user_id}
            )
            
            if guid_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким GUID уже существует"
                )
        
        # Обновляем пользователя
        query = """
            UPDATE users 
            SET guid = :guid, name = :name, 
                is_active = :is_active, is_admin = :is_admin, 
                department = :department, is_user = :is_user,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
            RETURNING id, guid, name, is_active, is_admin, department, is_user, 
                      created_at, updated_at, last_login_at
        """
        
        values = {
            "user_id": user_id,
            "guid": user_data.guid,
            "name": user_data.name,
            "is_active": user_data.is_active,
            "is_admin": user_data.is_admin,
            "department": user_data.department,
            "is_user": user_data.is_user
        }
        
        updated_user = await db.fetch_one(query=query, values=values)
        
        logger.info(f"USER_UPDATE → user_id={user_id}, name={user_data.name}")
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# Новые эндпоинты для управления владельцами справочников

@users_router.post("/{user_id}/dictionary-ownership", response_model=DictionaryOwnerOut)
async def add_dictionary_ownership(
    user_id: int,
    ownership_data: DictionaryOwnerIn,
    db: Database = Depends(get_database)
) -> Any:
    """
    Добавление права владения справочником для пользователя
    """
    try:
        # Проверяем, что пользователь не является администратором системы
        user_query = "SELECT is_admin FROM users WHERE id = :user_id"
        user_row = await db.fetch_one(query=user_query, values={"user_id": user_id})
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        if user_row["is_admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя назначать владельца справочника для администратора системы"
            )
        
        # Создаем запись о владении
        ownership_service = DictionaryOwnerService()
        result = await ownership_service.create_ownership(
            ownership_data.id_dictionary, 
            user_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка создания записи о владении"
            )
        
        logger.info(f"DICTIONARY_OWNERSHIP_ADD → user_id={user_id}, dict_id={ownership_data.id_dictionary}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка добавления права владения для пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.delete("/{user_id}/dictionary-ownership/{dictionary_id}")
async def remove_dictionary_ownership(
    user_id: int,
    dictionary_id: int
) -> Any:
    """
    Удаление права владения справочником для пользователя
    """
    try:
        ownership_service = DictionaryOwnerService()
        result = await ownership_service.delete_ownership(dictionary_id, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись о владении не найдена"
            )
        
        logger.info(f"DICTIONARY_OWNERSHIP_REMOVE → user_id={user_id}, dict_id={dictionary_id}")
        return {"success": True, "message": "Право владения удалено"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления права владения для пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/dictionaries/available", response_model=List[Dict[str, Any]])
async def get_available_dictionaries() -> Any:
    """
    Получение списка доступных справочников для назначения владельцев
    """
    try:
        ownership_service = DictionaryOwnerService()
        dictionaries = await ownership_service.get_all_dictionaries()
        
        logger.info(f"AVAILABLE_DICTIONARIES_GET → count={len(dictionaries)}")
        return dictionaries
        
    except Exception as e:
        logger.error(f"Ошибка получения списка доступных справочников: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/{user_id}/with-ownership", response_model=UserWithDictionaryOwnership)
async def get_user_with_ownership(
    user_id: int,
    db: Database = Depends(get_database)
) -> Any:
    """
    Получение информации о пользователе с данными о владении справочниками
    """
    try:
        # Получаем основную информацию о пользователе
        user_query = """
            SELECT id, guid, name, is_active, is_admin, department, is_user, 
                   created_at, updated_at, last_login_at
            FROM users WHERE id = :user_id
        """
        
        user_row = await db.fetch_one(query=user_query, values={"user_id": user_id})
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден"
            )
        
        # Получаем информацию о владении справочниками
        ownership_service = DictionaryOwnerService()
        ownership_list = await ownership_service.get_user_ownership(user_id)
        
        # Формируем ответ
        user_data = dict(user_row)
        user_data["dictionary_ownership"] = ownership_list
        
        logger.info(f"USER_WITH_OWNERSHIP_GET → user_id={user_id}, ownership_count={len(ownership_list)}")
        return UserWithDictionaryOwnership(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя с владением по ID {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/guid/{guid}", response_model=UserOut)
async def get_user_by_guid(
    guid: str,
    domain: Optional[str] = Query(None, description="Домен пользователя"),
    db: Database = Depends(get_database)
) -> Any:
    """
    Получение информации о пользователе по GUID (с опциональной фильтрацией по домену)
    """
    try:
        # Очищаем GUID от фигурных скобок
        clean_guid = guid.strip('{}')
        
        conditions = ["guid = :guid"]
        values = {"guid": clean_guid}
        
        if domain:
            conditions.append("domain = :domain")
            values["domain"] = domain
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT id, guid, name, is_active, is_admin, department, is_user, 
                   created_at, updated_at, last_login_at
            FROM users WHERE {where_clause}
        """
        
        user_row = await db.fetch_one(query=query, values=values)
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден"
            )
            
        logger.info(f"USER_GET_BY_GUID → guid={clean_guid}, domain={domain}")
        return UserOut(**user_row)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по GUID {guid}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.patch("/update-department")
async def update_user_department(
    update_data: dict,
    db: Database = Depends(get_database)
):
    """Обновление подразделения пользователя"""
    try:
        username = update_data.get("username")
        domain = update_data.get("domain")
        department = update_data.get("department")
        guid = update_data.get("guid")
        
        if not username or not domain or not department:
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать username, domain и department"
            )
        
        # Формируем условие для поиска пользователя
        if guid:
            # Если есть GUID, ищем по нему
            where_clause = "guid = :guid"
            params = {"guid": guid}
        else:
            # Иначе ищем по имени пользователя
            where_clause = "name = :username"
            params = {"username": username}
        
        # Обновляем подразделение пользователя
        query = f"""
            UPDATE users 
            SET department = :department, updated_at = NOW()
            WHERE {where_clause}
            RETURNING id, name, department, updated_at
        """
        
        result = await db.fetch_one(query, {**params, "department": department})
        
        if result:
            logger.info(f"Подразделение пользователя {username}@{domain} обновлено: {department}")
            return {
                "success": True,
                "message": "Подразделение обновлено",
                "user": {
                    "id": result["id"],
                    "name": result["name"],
                    "department": result["department"],
                    "updated_at": result["updated_at"]
                }
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления подразделения пользователя: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )

@users_router.post("/sync-departments")
async def sync_user_departments(
    sync_data: dict,
    db: Database = Depends(get_database)
):
    """Синхронизация подразделений пользователей из домена"""
    try:
        # Получаем данные для синхронизации
        users_data = sync_data.get("users", [])
        
        if not users_data:
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать данные пользователей для синхронизации"
            )
        
        updated_count = 0
        errors = []
        
        for user_data in users_data:
            try:
                username = user_data.get("username")
                domain = user_data.get("domain")
                department = user_data.get("department")
                guid = user_data.get("guid")
                
                if not username or not domain or not department:
                    errors.append(f"Неполные данные для пользователя: {user_data}")
                    continue
                
                # Ищем пользователя по GUID или имени
                if guid:
                    where_clause = "guid = :guid"
                    params = {"guid": guid}
                else:
                    where_clause = "name = :username"
                    params = {"username": username}
                
                # Обновляем подразделение
                update_query = f"""
                    UPDATE users 
                    SET department = :department, updated_at = NOW()
                    WHERE {where_clause}
                """
                
                result = await db.execute(update_query, {**params, "department": department})
                
                if result:
                    updated_count += 1
                    logger.info(f"Подразделение пользователя {username}@{domain} обновлено: {department}")
                
            except Exception as e:
                error_msg = f"Ошибка обновления пользователя {user_data}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            "success": True,
            "message": f"Синхронизация завершена. Обновлено: {updated_count}, ошибок: {len(errors)}",
            "updated_count": updated_count,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка синхронизации подразделений: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )
