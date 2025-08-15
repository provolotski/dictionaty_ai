"""
Схемы данных для API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict  # noqa: F401
from datetime import date, datetime


class DictionaryIn(BaseModel):
    """Схема для создания справочника"""
    name: str = Field(..., min_length=1, max_length=255, description="Название справочника")
    code: str = Field(..., min_length=1, max_length=50, description="Код справочника")
    description: str = Field(..., min_length=1, max_length=1000, description="Описание справочника")
    start_date: date = Field(..., description="Дата начала действия")
    finish_date: date = Field(..., description="Дата окончания действия")
    name_eng: Optional[str] = Field(None, max_length=255, description="Название на английском")
    name_bel: Optional[str] = Field(None, max_length=255, description="Название на белорусском")
    description_eng: Optional[str] = Field(None, max_length=1000, description="Описание на английском")
    description_bel: Optional[str] = Field(None, max_length=1000, description="Описание на белорусском")
    gko: Optional[str] = Field(None, max_length=100, description="ГКО")
    organization: Optional[str] = Field(None, max_length=255, description="Организация")
    classifier: Optional[str] = Field(None, max_length=100, description="Классификатор")
    id_type: int = Field(..., description="ID типа справочника")

    @validator('finish_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Дата окончания должна быть больше даты начала')
        return v

    @validator('code')
    def validate_code(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Код может содержать только буквы, цифры, подчеркивания и дефисы')
        return v


class DictionaryOut(BaseModel):
    """Схема для ответа со справочником"""
    id: int
    name: str
    code: str
    description: str
    start_date: date
    finish_date: date
    name_eng: Optional[str]
    name_bel: Optional[str]
    description_eng: Optional[str]
    description_bel: Optional[str]
    gko: Optional[str]
    organization: Optional[str]
    classifier: Optional[str]
    id_type: int
    id_status: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictionaryPosition(BaseModel):
    """Схема для позиции справочника"""
    id: int
    code: str
    name: str
    description: Optional[str]
    start_date: date
    finish_date: date
    parent_id: Optional[int]
    dictionary_id: int

    class Config:
        from_attributes = True


class AttributeIn(BaseModel):
    """Схема для входящего атрибута справочника"""
    id: int
    name: str
    type: str
    required: bool
    description: Optional[str]

    class Config:
        from_attributes = True


class AttributeDict(BaseModel):
    """Схема для атрибута справочника"""
    id: int
    name: str
    type: str
    required: bool
    description: Optional[str]

    class Config:
        from_attributes = True


class AttrShown(BaseModel):
    """Схема для отображения атрибута"""
    name: str
    value: Optional[str]


class DictionaryType(BaseModel):
    """Схема для типа справочника"""
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


# Схемы для аутентификации
class LoginRequest(BaseModel):
    """Схема для запроса входа"""
    username: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    password: str = Field(..., min_length=1, max_length=100, description="Пароль")


class TokenResponse(BaseModel):
    """Схема для ответа с токенами"""
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время жизни токена в секундах")
    user: dict = Field(..., description="Информация о пользователе")


class RefreshTokenRequest(BaseModel):
    """Схема для запроса обновления токена"""
    refresh_token: str = Field(..., description="Refresh token")


class UserInfo(BaseModel):
    """Схема для информации о пользователе"""
    username: str = Field(..., description="Имя пользователя")
    display_name: str = Field(..., description="Отображаемое имя")
    email: str = Field(..., description="Email")
    groups: List[str] = Field(default=[], description="Группы пользователя")
    department: str = Field(..., description="Отдел")
    title: str = Field(..., description="Должность")
    employee_id: str = Field(..., description="ID сотрудника")


class AuthError(BaseModel):
    """Схема для ошибки аутентификации"""
    detail: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")


class PasswordChangeRequest(BaseModel):
    """Схема для запроса смены пароля"""
    current_password: str = Field(..., min_length=1, description="Текущий пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль")
    confirm_password: str = Field(..., min_length=8, description="Подтверждение нового пароля")

    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Пароли не совпадают')
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Новый пароль должен содержать минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Новый пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.islower() for c in v):
            raise ValueError('Новый пароль должен содержать хотя бы одну строчную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Новый пароль должен содержать хотя бы одну цифру')
        return v


class GroupMembershipRequest(BaseModel):
    """Схема для запроса проверки членства в группе"""
    group_name: str = Field(..., min_length=1, description="Название группы")


class GroupMembershipResponse(BaseModel):
    """Схема для ответа о членстве в группе"""
    username: str = Field(..., description="Имя пользователя")
    group_name: str = Field(..., description="Название группы")
    is_member: bool = Field(..., description="Является ли пользователь членом группы")
    membership_type: Optional[str] = Field(None, description="Тип членства (прямое/вложенное)")


class UserSession(BaseModel):
    """Схема для сессии пользователя"""
    username: str = Field(..., description="Имя пользователя")
    login_time: datetime = Field(..., description="Время входа")
    last_activity: datetime = Field(..., description="Последняя активность")
    ip_address: Optional[str] = Field(None, description="IP адрес")
    user_agent: Optional[str] = Field(None, description="User Agent")
    is_active: bool = Field(default=True, description="Активна ли сессия")


class LogoutRequest(BaseModel):
    """Схема для запроса выхода"""
    refresh_token: str = Field(..., description="Refresh token для инвалидации")


class AuthStatus(BaseModel):
    """Схема для статуса аутентификации"""
    is_authenticated: bool = Field(..., description="Аутентифицирован ли пользователь")
    user: Optional[UserInfo] = Field(None, description="Информация о пользователе")
    session_expires_at: Optional[datetime] = Field(None, description="Время истечения сессии")
    permissions: List[str] = Field(default=[], description="Разрешения пользователя")


class ActionLogIn(BaseModel):
    """Схема входящих данных для записи аудита действий"""
    guid: Optional[str] = Field(None, description="GUID пользователя (для апсерта в таблицу users)")
    username: str = Field(..., description="Имя пользователя")
    domain: str = Field(..., description="Домен")
    ip_address: str = Field(..., description="IP адрес")
    user_agent: str = Field(..., description="User Agent")
    action: str = Field(..., description="Действие")
    status: str = Field(..., description="Статус действия")
    comment: Optional[str] = Field(None, description="Комментарий")


class ActionLogOut(BaseModel):
    """Схема ответа после записи аудита"""
    id: int = Field(..., description="ID записи")
    username: str
    domain: str
    ip_address: str
    user_agent: str
    action: str
    datetime: datetime
    status: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class ActionLogStats(BaseModel):
    """Статистика по логам аудита"""
    total: int = Field(..., description="Общее количество записей")
    counts_by_status: Dict[str, int] = Field(default_factory=dict, description="Количество по статусам")
    counts_by_action: Dict[str, int] = Field(default_factory=dict, description="Количество по действиям")


class UserOut(BaseModel):
    """Схема для отображения пользователя"""
    id: int = Field(..., description="ID пользователя")
    guid: str = Field(..., description="GUID пользователя")
    name: str = Field(..., description="Имя пользователя")
    domain: str = Field(..., description="Домен")
    created_at: datetime = Field(..., description="Дата создания")
    last_login_at: datetime = Field(..., description="Дата последнего входа")
    is_admin: bool = Field(default=False, description="Признак администратора системы")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Схема ответа со списком пользователей"""
    users: List[UserOut] = Field(..., description="Список пользователей")
    total: int = Field(..., description="Общее количество пользователей")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    total_pages: int = Field(..., description="Общее количество страниц")