"""
Пользовательские исключения для приложения
"""

from typing import Any, Dict, Optional


class DictionaryAPIException(Exception):
    """Базовое исключение для API справочников"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionError(DictionaryAPIException):
    """Ошибка подключения к базе данных"""
    
    def __init__(self, message: str = "Ошибка подключения к базе данных"):
        super().__init__(message, status_code=503)


class DictionaryNotFoundError(DictionaryAPIException):
    """Справочник не найден"""
    
    def __init__(self, dictionary_id: int):
        super().__init__(
            f"Справочник с ID {dictionary_id} не найден",
            status_code=404,
            details={"dictionary_id": dictionary_id}
        )


class DictionaryValidationError(DictionaryAPIException):
    """Ошибка валидации данных справочника"""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        super().__init__(
            message,
            status_code=422,
            details={"field_errors": field_errors or {}}
        )


class AttributeNotFoundError(DictionaryAPIException):
    """Атрибут не найден"""
    
    def __init__(self, attribute_id: int):
        super().__init__(
            f"Атрибут с ID {attribute_id} не найден",
            status_code=404,
            details={"attribute_id": attribute_id}
        )


class PositionNotFoundError(DictionaryAPIException):
    """Позиция справочника не найдена"""
    
    def __init__(self, position_id: int):
        super().__init__(
            f"Позиция с ID {position_id} не найдена",
            status_code=404,
            details={"position_id": position_id}
        )


class FileProcessingError(DictionaryAPIException):
    """Ошибка обработки файла"""
    
    def __init__(self, message: str, file_name: Optional[str] = None):
        super().__init__(
            message,
            status_code=400,
            details={"file_name": file_name}
        )


class DuplicateCodeError(DictionaryAPIException):
    """Дублирование кода"""
    
    def __init__(self, code: str, entity_type: str = "справочник"):
        super().__init__(
            f"{entity_type.capitalize()} с кодом '{code}' уже существует",
            status_code=409,
            details={"code": code, "entity_type": entity_type}
        ) 