from fastapi import APIRouter, Depends, HTTPException, status, Query
from databases import Database
from typing import Any, List, Optional, Dict
from datetime import datetime

from database import get_database
from schemas import ActionLogIn, ActionLogOut, ActionLogStats
from utils.logger import setup_logger

logger = setup_logger(__name__)

audit_router = APIRouter(prefix="/audit", tags=["audit"]) 


@audit_router.post("/log", response_model=ActionLogOut, status_code=status.HTTP_201_CREATED)
async def create_action_log(payload: ActionLogIn, db: Database = Depends(get_database)) -> Any:
    """
    Запись события аудита в таблицу action_log
    """
    try:
        query = (
            "INSERT INTO action_log (username, domain, ip_address, user_agent, action, status, comment) "
            "VALUES (:username, :domain, :ip_address, :user_agent, :action, :status, :comment) "
            "RETURNING id, username, domain, ip_address, user_agent, action, datetime, status, comment"
        )

        values = {
            "username": payload.username,
            "domain": payload.domain,
            "ip_address": payload.ip_address,
            "user_agent": payload.user_agent,
            "action": payload.action,
            "status": payload.status,
            "comment": payload.comment,
        }

        logger.info(f"AUDIT_LOG request → values={values}")

        row = await db.fetch_one(query=query, values=values)
        if not row:
            raise HTTPException(status_code=500, detail="Не удалось создать запись аудита")

        result = ActionLogOut(**row)
        logger.info(f"AUDIT_LOG created ← id={result.id}, action={result.action}, status={result.status}")

        # Если событие успешного логина — выполняем UPSERT пользователя в таблицу users
        try:
            is_success_login = (payload.action.lower() in [
                'логин пользователя', 'user_login', 'login', 'login_success'
            ]) and (payload.status.lower() in ['успешно', 'success'])

            if is_success_login:
                # Некоторые клиенты могут не прислать guid — обрабатываем мягко
                guid_value = None
                try:
                    guid_value = getattr(payload, 'guid', None)
                    if isinstance(guid_value, str):
                        guid_value = guid_value.strip('{}').strip()
                except Exception:
                    guid_value = None

                if guid_value and payload.domain:
                    # Пытаемся сначала обновить существующего пользователя
                    update_sql = (
                        "UPDATE users SET name = :name, last_login_at = NOW() "
                        "WHERE guid = :guid AND domain = :domain RETURNING id"
                    )
                    values_update = {
                        'guid': guid_value,
                        'name': payload.username,
                        'domain': payload.domain,
                    }
                    updated_row = None
                    try:
                        updated_row = await db.fetch_one(query=update_sql, values=values_update)
                    except Exception as user_e:
                        logger.error(f"Ошибка UPDATE пользователя: {user_e}")
                        updated_row = None

                    if updated_row is None:
                        # Если не нашли — вставляем нового
                        insert_sql = (
                            "INSERT INTO users (guid, name, domain, created_at, last_login_at,is_admin) "
                            "VALUES (:guid, :name, :domain, NOW(), NOW(), false)"
                        )
                        try:
                            await db.execute(query=insert_sql, values=values_update)
                            logger.info(f"USERS INSERT ← guid={guid_value} domain={payload.domain} name={payload.username}")
                        except Exception as user_e2:
                            logger.error(f"Ошибка INSERT пользователя: {user_e2}")
                else:
                    logger.debug("Пропущен UPSERT пользователя: отсутствует guid или domain")
        except Exception as e2:
            logger.error(f"Ошибка пост-обработки успешного логина: {e2}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка записи аудита: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@audit_router.get("/logs", response_model=List[ActionLogOut])
async def get_action_logs(
    db: Database = Depends(get_database),
    date_from: Optional[str] = Query(None, description="ISO дата начала, например 2025-08-14T00:00:00"),
    date_to: Optional[str] = Query(None, description="ISO дата конца, например 2025-08-15T00:00:00"),
    status_filter: Optional[List[str]] = Query(None, alias="status", description="Фильтр по статусам, множественные"),
    action_filter: Optional[List[str]] = Query(None, alias="action", description="Фильтр по действиям, множественные"),
    users: Optional[List[str]] = Query(None, alias="username", description="Фильтр по пользователям, множественные"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Any:
    """
    Получение записей аудита с фильтрацией по датам, статусам, действиям и пользователям
    """
    try:
        conditions = []
        values: Dict[str, Any] = {}

        if date_from:
            conditions.append("datetime >= :date_from")
            values["date_from"] = datetime.fromisoformat(date_from)
        if date_to:
            conditions.append("datetime <= :date_to")
            values["date_to"] = datetime.fromisoformat(date_to)
        if status_filter:
            conditions.append("status = ANY(:status)")
            values["status"] = status_filter
        if action_filter:
            conditions.append("action = ANY(:action)")
            values["action"] = action_filter
        if users:
            conditions.append("username = ANY(:users)")
            values["users"] = users

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = (
            "SELECT id, username, domain, ip_address, user_agent, action, datetime, status, comment "
            f"FROM action_log {where_clause} "
            "ORDER BY datetime DESC "
            "LIMIT :limit OFFSET :offset"
        )
        values["limit"] = limit
        values["offset"] = offset

        rows = await db.fetch_all(query=query, values=values)
        return [ActionLogOut(**row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения логов аудита: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@audit_router.get("/stats", response_model=ActionLogStats)
async def get_action_logs_stats(
    db: Database = Depends(get_database),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
) -> Any:
    """
    Получение статистики по логам аудита (общее количество, по статусам, по действиям)
    """
    try:
        values: Dict[str, Any] = {}
        where_parts = []
        if date_from:
            where_parts.append("datetime >= :date_from")
            values["date_from"] = datetime.fromisoformat(date_from)
        if date_to:
            where_parts.append("datetime <= :date_to")
            values["date_to"] = datetime.fromisoformat(date_to)
        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        total_q = f"SELECT COUNT(*) AS cnt FROM action_log {where_clause}"
        total_row = await db.fetch_one(total_q, values)
        total = total_row["cnt"] if total_row else 0

        by_status_q = f"SELECT status, COUNT(*) AS cnt FROM action_log {where_clause} GROUP BY status"
        by_action_q = f"SELECT action, COUNT(*) AS cnt FROM action_log {where_clause} GROUP BY action"

        by_status_rows = await db.fetch_all(by_status_q, values)
        by_action_rows = await db.fetch_all(by_action_q, values)

        counts_by_status = {r["status"]: r["cnt"] for r in by_status_rows}
        counts_by_action = {r["action"]: r["cnt"] for r in by_action_rows}

        return ActionLogStats(total=total, counts_by_status=counts_by_status, counts_by_action=counts_by_action)
    except Exception as e:
        logger.error(f"Ошибка получения статистики аудита: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
