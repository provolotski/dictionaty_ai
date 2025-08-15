"""
Сервисный слой для работы со справочниками
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
import pandas as pd
from databases import Database

from models.model_dictionary import DictionaryService as DictionaryModel
from models.model_attribute import AttributeManager
from schemas import DictionaryIn, DictionaryOut, DictionaryPosition, AttributeDict
from exceptions import (
    DictionaryNotFoundError,
    DictionaryValidationError,
    DuplicateCodeError,
    FileProcessingError
)
from utils.logger import setup_logger
from cache.cache_manager import cached, invalidate_cache, cache_manager

logger = setup_logger(__name__)


class DictionaryService:
    """
    Сервис для работы со справочниками
    """
    
    def __init__(self, database: Database):
        self.database = database
        self.model = DictionaryModel()
        self.attribute_manager = AttributeManager()
    
    @invalidate_cache("dictionary")  # Инвалидируем кэш справочников
    async def create_dictionary(self, dictionary: DictionaryIn) -> int:
        """
        Создание нового справочника
        
        Args:
            dictionary: Данные справочника
            
        Returns:
            int: ID созданного справочника
            
        Raises:
            DictionaryValidationError: Ошибка валидации
            DuplicateCodeError: Дублирование кода
        """
        try:
            # Валидация дат
            if dictionary.start_date >= dictionary.finish_date:
                raise DictionaryValidationError(
                    "Дата начала должна быть меньше даты окончания"
                )
            
            # Проверка на дублирование кода
            existing = await self.find_dictionary_by_code(dictionary.code)
            if existing:
                raise DuplicateCodeError(dictionary.code)
            
            # Установка статуса
            if dictionary.start_date <= date.today() <= dictionary.finish_date:
                dictionary.id_status = 1
            else:
                dictionary.id_status = 0
            
            # Создание справочника
            dictionary_id = await self.model.create(dictionary)
            logger.info(f"Создан справочник с ID: {dictionary_id}")
            
            return dictionary_id
            
        except (DictionaryValidationError, DuplicateCodeError):
            raise
        except Exception as e:
            logger.error(f"Ошибка создания справочника: {e}")
            raise DictionaryValidationError(f"Ошибка создания справочника: {str(e)}")
    
    @cached("dictionary_by_id", ttl=1800)  # 30 минут
    async def get_dictionary(self, dictionary_id: int) -> DictionaryOut:
        """
        Получение справочника по ID
        
        Args:
            dictionary_id: ID справочника
            
        Returns:
            DictionaryOut: Данные справочника
            
        Raises:
            DictionaryNotFoundError: Справочник не найден
        """
        try:
            dictionary = await self.model.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                raise DictionaryNotFoundError(dictionary_id)
            return dictionary
        except DictionaryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения справочника {dictionary_id}: {e}")
            raise DictionaryNotFoundError(dictionary_id)
    
    @cached("all_dictionaries", ttl=900)  # 15 минут
    async def get_all_dictionaries(self) -> List[DictionaryOut]:
        """
        Получение всех справочников
        
        Returns:
            List[DictionaryOut]: Список справочников
        """
        try:
            return await self.model.get_all()
        except Exception as e:
            logger.error(f"Ошибка получения списка справочников: {e}")
            return []
    
    @invalidate_cache("dictionary")  # Инвалидируем кэш справочников
    async def update_dictionary(self, dictionary_id: int, dictionary: DictionaryIn) -> bool:
        """
        Обновление справочника
        
        Args:
            dictionary_id: ID справочника
            dictionary: Новые данные
            
        Returns:
            bool: True если обновление успешно
            
        Raises:
            DictionaryNotFoundError: Справочник не найден
        """
        try:
            # Проверяем существование справочника
            existing = await self.get_dictionary(dictionary_id)
            if not existing:
                raise DictionaryNotFoundError(dictionary_id)
            
            # Валидация дат
            if dictionary.start_date >= dictionary.finish_date:
                raise DictionaryValidationError(
                    "Дата начала должна быть меньше даты окончания"
                )
            
            # Обновление статуса
            if dictionary.start_date <= date.today() <= dictionary.finish_date:
                dictionary.id_status = 1
            else:
                dictionary.id_status = 0
            
            success = await self.model.update(dictionary_id, dictionary)
            if success:
                logger.info(f"Обновлен справочник с ID: {dictionary_id}")
            
            return success
            
        except (DictionaryNotFoundError, DictionaryValidationError):
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления справочника {dictionary_id}: {e}")
            raise DictionaryValidationError(f"Ошибка обновления справочника: {str(e)}")
    
    @invalidate_cache("dictionary")  # Инвалидируем кэш справочников
    async def delete_dictionary(self, dictionary_id: int) -> bool:
        """
        Удаление справочника
        
        Args:
            dictionary_id: ID справочника
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            DictionaryNotFoundError: Справочник не найден
        """
        try:
            # Проверяем существование справочника
            existing = await self.get_dictionary(dictionary_id)
            if not existing:
                raise DictionaryNotFoundError(dictionary_id)
            
            # Проверяем возможность удаления
            can_delete = await self.model.can_delete_dictionary(dictionary_id)
            if not can_delete:
                raise DictionaryValidationError(
                    "Невозможно удалить справочник с существующими позициями"
                )
            
            success = await self.model.delete_dictionary_by_id(dictionary_id)
            if success:
                logger.info(f"Удален справочник с ID: {dictionary_id}")
            
            return success
            
        except (DictionaryNotFoundError, DictionaryValidationError):
            raise
        except Exception as e:
            logger.error(f"Ошибка удаления справочника {dictionary_id}: {e}")
            raise DictionaryValidationError(f"Ошибка удаления справочника: {str(e)}")
    
    async def find_dictionary_by_name(self, name: str) -> List[DictionaryOut]:
        """
        Поиск справочников по названию
        
        Args:
            name: Название для поиска
            
        Returns:
            List[DictionaryOut]: Список найденных справочников
        """
        try:
            return await self.model.find_dictionary_by_name(name)
        except Exception as e:
            logger.error(f"Ошибка поиска справочников по названию '{name}': {e}")
            return []
    
    async def find_dictionary_by_code(self, code: str) -> Optional[DictionaryOut]:
        """
        Поиск справочника по коду
        
        Args:
            code: Код справочника
            
        Returns:
            Optional[DictionaryOut]: Найденный справочник или None
        """
        try:
            dictionaries = await self.model.find_dictionary_by_name(code)
            for dictionary in dictionaries:
                if dictionary.code == code:
                    return dictionary
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска справочника по коду '{code}': {e}")
            return None
    
    @cached("dictionary_values", ttl=600)  # 10 минут
    async def get_dictionary_values(
        self, 
        dictionary_id: int, 
        target_date: Optional[date] = None
    ) -> List[DictionaryPosition]:
        """
        Получение значений справочника
        
        Args:
            dictionary_id: ID справочника
            target_date: Дата для получения значений (по умолчанию текущая)
            
        Returns:
            List[DictionaryPosition]: Список позиций справочника
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            return await self.model.get_dictionary_values(dictionary_id, target_date)
        except Exception as e:
            logger.error(f"Ошибка получения значений справочника {dictionary_id}: {e}")
            return []
    
    @invalidate_cache("dictionary_values")  # Инвалидируем кэш значений справочника
    async def import_csv_data(
        self, 
        dictionary_id: int, 
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Импорт данных из CSV файла
        
        Args:
            dictionary_id: ID справочника
            file_content: Содержимое файла
            filename: Имя файла
            
        Returns:
            Dict[str, Any]: Результат импорта
            
        Raises:
            FileProcessingError: Ошибка обработки файла
        """
        try:
            # Декодирование файла
            encodings = ["utf-8", "windows-1251", "cp1252", "iso-8859-1"]
            content = None
            
            for encoding in encodings:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise FileProcessingError(
                    "Не удалось декодировать файл",
                    filename
                )
            
            import io
            
            # Чтение CSV
            df = pd.read_csv(
                io.StringIO(content),
                sep=';',
                encoding='utf-8',
                dtype=str
            )
            
            # Валидация структуры
            if df.empty:
                raise FileProcessingError(
                    "Файл не содержит данных",
                    filename
                )
            
            # Импорт данных
            success = await self.model.insert_dictionary_values(dictionary_id, df)
            
            if success:
                logger.info(f"Импортировано {len(df)} записей в справочник {dictionary_id}")
                return {
                    "message": f"Импортировано {len(df)} записей",
                    "imported_count": len(df)
                }
            else:
                raise FileProcessingError(
                    "Ошибка при импорте данных",
                    filename
                )
                
        except FileProcessingError:
            raise
        except Exception as e:
            logger.error(f"Ошибка импорта CSV в справочник {dictionary_id}: {e}")
            raise FileProcessingError(
                f"Ошибка обработки файла: {str(e)}",
                filename
            ) 