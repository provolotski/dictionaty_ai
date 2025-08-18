"""
Роутер для управления пользователями системы
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from databases import Database
from typing import Any, List, Optional, Dict
from datetime import datetime
import math

from database import get_database
from schemas import UserOut, UserListResponse
from utils.logger import setup_logger

logger = setup_logger(__name__)

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/", response_model=UserListResponse)
async def get_users(
    db: Database = Depends(get_database),
    domain: Optional[str] = Query(None, description="Фильтр по домену"),
    search: Optional[str] = Query(None, description="Поиск по имени пользователя"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(25, ge=1, le=100, description="Размер страницы")
) -> Any:
    """
    Получение списка всех пользователей с пагинацией и фильтрацией
    """
    try:
        # Формируем условия WHERE
        conditions = []
        values: Dict[str, Any] = {}
        
        if domain:
            conditions.append("domain = :domain")
            values["domain"] = domain
            
        if search:
            conditions.append("name ILIKE :search")
            values["search"] = f"%{search}%"
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Получаем общее количество пользователей
        count_query = f"SELECT COUNT(*) as total FROM users {where_clause}"
        count_result = await db.fetch_one(query=count_query, values=values)
        total_users = count_result["total"] if count_result else 0
        
        # Вычисляем пагинацию
        total_pages = math.ceil(total_users / page_size)
        offset = (page - 1) * page_size
        
        # Получаем пользователей для текущей страницы
        users_query = (
            f"SELECT id, guid, name, domain, created_at, last_login_at, is_admin "
            f"FROM users {where_clause} "
            f"ORDER BY last_login_at DESC, name ASC "
            f"LIMIT :page_size OFFSET :offset"
        )
        
        values["page_size"] = page_size
        values["offset"] = offset
        
        users_rows = await db.fetch_all(query=users_query, values=values)
        
        # Преобразуем в Pydantic модели
        users = [UserOut(**row) for row in users_rows]
        
        logger.info(f"USERS_GET → domain={domain}, search={search}, page={page}, page_size={page_size}, total={total_users}")
        
        return UserListResponse(
            users=users,
            total=total_users,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@users_router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: int,
    db: Database = Depends(get_database)
) -> Any:
    """
    Получение информации о конкретном пользователе по ID
    """
    try:
        query = (
            "SELECT id, guid, name, domain, created_at, last_login_at, is_admin "
            "FROM users WHERE id = :user_id"
        )
        
        user_row = await db.fetch_one(query=query, values={"user_id": user_id})
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден"
            )
            
        logger.info(f"USER_GET_BY_ID → user_id={user_id}")
        return UserOut(**user_row)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по ID {user_id}: {e}")
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
        
        query = (
            f"SELECT id, guid, name, domain, created_at, last_login_at, is_admin "
            f"FROM users WHERE {where_clause}"
        )
        
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


@users_router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Database = Depends(get_database)
) -> Any:
    """
    Обновление информации о пользователе
    """
    try:
        # Проверяем, что пользователь существует
        check_query = "SELECT id FROM users WHERE id = :user_id"
        existing_user = await db.fetch_one(query=check_query, values={"user_id": user_id})
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден"
            )
        
        # Обновляем только разрешенные поля
        allowed_fields = ['name', 'is_admin']
        update_fields = []
        values = {"user_id": user_id}
        
        for field in allowed_fields:
            if field in user_data:
                update_fields.append(f"{field} = :{field}")
                values[field] = user_data[field]
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет полей для обновления"
            )
        
        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :user_id RETURNING id, guid, name, domain, created_at, last_login_at, is_admin"
        
        updated_user = await db.fetch_one(query=update_query, values=values)
        
        logger.info(f"USER_UPDATE → user_id={user_id}, fields={list(user_data.keys())}")
        return UserOut(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
