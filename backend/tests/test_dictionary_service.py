"""
Тесты для сервисного слоя справочников
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Optional

from services.dictionary_service import DictionaryService
from models.model_dictionary import DictionaryService as DictionaryModel
from models.model_attribute import AttributeManager
from schemas import DictionaryIn, DictionaryOut, DictionaryPosition
from exceptions import (
    DictionaryNotFoundError,
    DictionaryValidationError,
    DuplicateCodeError,
    FileProcessingError
)


class TestDictionaryService:
    """Тесты для класса DictionaryService"""

    @pytest.fixture
    def mock_database(self):
        """Мок для базы данных"""
        return AsyncMock()

    @pytest.fixture
    def dictionary_service(self, mock_database):
        """Экземпляр сервиса с мок-базой данных"""
        with patch("services.dictionary_service.DictionaryModel") as mock_model, \
             patch("services.dictionary_service.AttributeManager") as mock_attr_manager:
            service = DictionaryService(mock_database)
            service.model = mock_model.return_value
            service.attribute_manager = mock_attr_manager.return_value
            return service

    @pytest.fixture
    def sample_dictionary_in(self):
        """Тестовые данные для создания справочника"""
        return DictionaryIn(
            name="Test Dictionary",
            code="test_001",
            description="Test description",
            start_date=date(2024, 1, 1),
            finish_date=date(2024, 12, 31),
            name_eng="Test Dictionary",
            name_bel="Тэставы даведнік",
            description_eng="Test description",
            description_bel="Тэставае апісанне",
            gko="Test GKO",
            organization="Test Org",
            classifier="Test Classifier",
            id_type=1
        )

    @pytest.fixture
    def sample_dictionary_out(self):
        """Тестовые данные справочника для ответа"""
        return DictionaryOut(
            id=1,
            name="Test Dictionary",
            code="test_001",
            description="Test description",
            start_date=date(2024, 1, 1),
            finish_date=date(2024, 12, 31),
            name_eng="Test Dictionary",
            name_bel="Тэставы даведнік",
            description_eng="Test description",
            description_bel="Тэставае апісанне",
            gko="Test GKO",
            organization="Test Org",
            classifier="Test Classifier",
            id_type=1,
            id_status=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    class TestCreateDictionary:
        """Тесты для создания справочника"""

        @pytest.mark.asyncio
        async def test_create_dictionary_success(self, dictionary_service, sample_dictionary_in):
            """Успешное создание справочника"""
            # Arrange
            dictionary_service.model.create.return_value = 1
            dictionary_service.find_dictionary_by_code.return_value = None

            # Act
            result = await dictionary_service.create_dictionary(sample_dictionary_in)

            # Assert
            assert result == 1
            dictionary_service.model.create.assert_awaited_once()
            dictionary_service.find_dictionary_by_code.assert_awaited_once_with("test_001")

        @pytest.mark.asyncio
        async def test_create_dictionary_invalid_dates(self, dictionary_service, sample_dictionary_in):
            """Создание справочника с некорректными датами"""
            # Arrange
            sample_dictionary_in.start_date = date(2024, 12, 31)
            sample_dictionary_in.finish_date = date(2024, 1, 1)

            # Act & Assert
            with pytest.raises(DictionaryValidationError, match="Дата начала должна быть меньше даты окончания"):
                await dictionary_service.create_dictionary(sample_dictionary_in)

        @pytest.mark.asyncio
        async def test_create_dictionary_duplicate_code(self, dictionary_service, sample_dictionary_in):
            """Создание справочника с дублирующимся кодом"""
            # Arrange
            dictionary_service.find_dictionary_by_code.return_value = sample_dictionary_in

            # Act & Assert
            with pytest.raises(DuplicateCodeError):
                await dictionary_service.create_dictionary(sample_dictionary_in)

        @pytest.mark.asyncio
        async def test_create_dictionary_database_error(self, dictionary_service, sample_dictionary_in):
            """Ошибка базы данных при создании справочника"""
            # Arrange
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(DictionaryValidationError, match="Ошибка создания справочника"):
                await dictionary_service.create_dictionary(sample_dictionary_in)

    class TestGetDictionary:
        """Тесты для получения справочника"""

        @pytest.mark.asyncio
        async def test_get_dictionary_success(self, dictionary_service, sample_dictionary_out):
            """Успешное получение справочника"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = sample_dictionary_out

            # Act
            result = await dictionary_service.get_dictionary(1)

            # Assert
            assert result == sample_dictionary_out
            dictionary_service.model.get_dictionary_by_id.assert_awaited_once_with(1)

        @pytest.mark.asyncio
        async def test_get_dictionary_not_found(self, dictionary_service):
            """Справочник не найден"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = None

            # Act & Assert
            with pytest.raises(DictionaryNotFoundError):
                await dictionary_service.get_dictionary(999)

    class TestGetAllDictionaries:
        """Тесты для получения всех справочников"""

        @pytest.mark.asyncio
        async def test_get_all_dictionaries_success(self, dictionary_service, sample_dictionary_out):
            """Успешное получение всех справочников"""
            # Arrange
            dictionaries = [sample_dictionary_out]
            dictionary_service.model.get_all_dictionaries.return_value = dictionaries

            # Act
            result = await dictionary_service.get_all_dictionaries()

            # Assert
            assert result == dictionaries
            dictionary_service.model.get_all_dictionaries.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_get_all_dictionaries_empty(self, dictionary_service):
            """Получение пустого списка справочников"""
            # Arrange
            dictionary_service.model.get_all_dictionaries.return_value = []

            # Act
            result = await dictionary_service.get_all_dictionaries()

            # Assert
            assert result == []
            dictionary_service.model.get_all_dictionaries.assert_awaited_once()

    class TestUpdateDictionary:
        """Тесты для обновления справочника"""

        @pytest.mark.asyncio
        async def test_update_dictionary_success(self, dictionary_service, sample_dictionary_in):
            """Успешное обновление справочника"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = sample_dictionary_in
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.update.return_value = True

            # Act
            result = await dictionary_service.update_dictionary(1, sample_dictionary_in)

            # Assert
            assert result is True
            dictionary_service.model.update.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_update_dictionary_not_found(self, dictionary_service, sample_dictionary_in):
            """Обновление несуществующего справочника"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = None

            # Act & Assert
            with pytest.raises(DictionaryNotFoundError):
                await dictionary_service.update_dictionary(999, sample_dictionary_in)

    class TestDeleteDictionary:
        """Тесты для удаления справочника"""

        @pytest.mark.asyncio
        async def test_delete_dictionary_success(self, dictionary_service):
            """Успешное удаление справочника"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = {"id": 1}
            dictionary_service.model.delete.return_value = True

            # Act
            result = await dictionary_service.delete_dictionary(1)

            # Assert
            assert result is True
            dictionary_service.model.delete.assert_awaited_once_with(1)

        @pytest.mark.asyncio
        async def test_delete_dictionary_not_found(self, dictionary_service):
            """Удаление несуществующего справочника"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.return_value = None

            # Act & Assert
            with pytest.raises(DictionaryNotFoundError):
                await dictionary_service.delete_dictionary(999)

    class TestFindDictionary:
        """Тесты для поиска справочников"""

        @pytest.mark.asyncio
        async def test_find_dictionary_by_name_success(self, dictionary_service, sample_dictionary_out):
            """Успешный поиск по имени"""
            # Arrange
            dictionaries = [sample_dictionary_out]
            dictionary_service.model.find_by_name.return_value = dictionaries

            # Act
            result = await dictionary_service.find_dictionary_by_name("Test")

            # Assert
            assert result == dictionaries
            dictionary_service.model.find_by_name.assert_awaited_once_with("Test")

        @pytest.mark.asyncio
        async def test_find_dictionary_by_code_success(self, dictionary_service, sample_dictionary_out):
            """Успешный поиск по коду"""
            # Arrange
            dictionary_service.model.find_by_code.return_value = sample_dictionary_out

            # Act
            result = await dictionary_service.find_dictionary_by_code("test_001")

            # Assert
            assert result == sample_dictionary_out
            dictionary_service.model.find_by_code.assert_awaited_once_with("test_001")

        @pytest.mark.asyncio
        async def test_find_dictionary_by_code_not_found(self, dictionary_service):
            """Поиск по коду - не найдено"""
            # Arrange
            dictionary_service.model.find_by_code.return_value = None

            # Act
            result = await dictionary_service.find_dictionary_by_code("nonexistent")

            # Assert
            assert result is None

    class TestGetDictionaryValues:
        """Тесты для получения значений справочника"""

        @pytest.mark.asyncio
        async def test_get_dictionary_values_success(self, dictionary_service):
            """Успешное получение значений справочника"""
            # Arrange
            positions = [{"id": 1, "code": "A1", "name": "Item 1"}]
            dictionary_service.model.get_dictionary_positions.return_value = positions

            # Act
            result = await dictionary_service.get_dictionary_values(1)

            # Assert
            assert result == positions
            dictionary_service.model.get_dictionary_positions.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_get_dictionary_values_with_date(self, dictionary_service):
            """Получение значений справочника с указанной датой"""
            # Arrange
            target_date = date(2024, 6, 1)
            positions = [{"id": 1, "code": "A1", "name": "Item 1"}]
            dictionary_service.model.get_dictionary_positions.return_value = positions

            # Act
            result = await dictionary_service.get_dictionary_values(1, target_date)

            # Assert
            assert result == positions
            dictionary_service.model.get_dictionary_positions.assert_awaited_once_with(1, target_date)

    class TestImportCsvData:
        """Тесты для импорта CSV данных"""

        @pytest.mark.asyncio
        async def test_import_csv_data_success(self, dictionary_service):
            """Успешный импорт CSV данных"""
            # Arrange
            file_content = b"CODE,NAME\nA1,Item 1\nA2,Item 2"
            filename = "test.csv"
            expected_result = {"imported": 2, "errors": 0}

            with patch("services.dictionary_service.pd.read_csv") as mock_read_csv, \
                 patch("services.dictionary_service.AttributeManager.import_data") as mock_import:
                mock_read_csv.return_value = MagicMock()
                mock_import.return_value = expected_result

                # Act
                result = await dictionary_service.import_csv_data(1, file_content, filename)

                # Assert
                assert result == expected_result
                mock_import.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_import_csv_data_invalid_file(self, dictionary_service):
            """Импорт некорректного файла"""
            # Arrange
            file_content = b"invalid content"
            filename = "test.txt"

            # Act & Assert
            with pytest.raises(FileProcessingError, match="Неподдерживаемый формат файла"):
                await dictionary_service.import_csv_data(1, file_content, filename)

        @pytest.mark.asyncio
        async def test_import_csv_data_processing_error(self, dictionary_service):
            """Ошибка обработки CSV файла"""
            # Arrange
            file_content = b"CODE,NAME\nA1,Item 1"
            filename = "test.csv"

            with patch("services.dictionary_service.pd.read_csv") as mock_read_csv:
                mock_read_csv.side_effect = Exception("CSV processing error")

                # Act & Assert
                with pytest.raises(FileProcessingError, match="Ошибка обработки файла"):
                    await dictionary_service.import_csv_data(1, file_content, filename)

    class TestGetDictionaryStructure:
        """Тесты для получения структуры справочника"""

        @pytest.mark.asyncio
        async def test_get_dictionary_structure_success(self, dictionary_service):
            """Успешное получение структуры справочника"""
            # Arrange
            structure = [{"id": 1, "name": "CODE", "type": "string"}]
            dictionary_service.model.get_dictionary_structure.return_value = structure

            # Act
            result = await dictionary_service.get_dictionary_structure(1)

            # Assert
            assert result == structure
            dictionary_service.model.get_dictionary_structure.assert_awaited_once_with(1)

    class TestGetDictionaryPosition:
        """Тесты для получения позиций справочника"""

        @pytest.mark.asyncio
        async def test_get_dictionary_position_by_code_success(self, dictionary_service):
            """Успешное получение позиции по коду"""
            # Arrange
            position = {"id": 1, "code": "A1", "name": "Item 1"}
            dictionary_service.model.get_position_by_code.return_value = position

            # Act
            result = await dictionary_service.get_dictionary_position_by_code(1, "A1")

            # Assert
            assert result == position
            dictionary_service.model.get_position_by_code.assert_awaited_once_with(1, "A1")

        @pytest.mark.asyncio
        async def test_get_dictionary_position_by_id_success(self, dictionary_service):
            """Успешное получение позиции по ID"""
            # Arrange
            position = {"id": 1, "code": "A1", "name": "Item 1"}
            dictionary_service.model.get_position_by_id.return_value = position

            # Act
            result = await dictionary_service.get_dictionary_position_by_id(1, 1)

            # Assert
            assert result == position
            dictionary_service.model.get_position_by_id.assert_awaited_once_with(1, 1)

    class TestFindDictionaryValue:
        """Тесты для поиска значений справочника"""

        @pytest.mark.asyncio
        async def test_find_dictionary_value_success(self, dictionary_service):
            """Успешный поиск значений справочника"""
            # Arrange
            values = [{"id": 1, "code": "A1", "name": "Item 1"}]
            dictionary_service.model.find_positions.return_value = values

            # Act
            result = await dictionary_service.find_dictionary_value(1, "Item")

            # Assert
            assert result == values
            dictionary_service.model.find_positions.assert_awaited_once_with(1, "Item")


class TestDictionaryServiceIntegration:
    """Интеграционные тесты для DictionaryService"""

    @pytest.mark.asyncio
    async def test_full_dictionary_lifecycle(self):
        """Полный жизненный цикл справочника"""
        # Arrange
        mock_database = AsyncMock()
        with patch("services.dictionary_service.DictionaryModel") as mock_model, \
             patch("services.dictionary_service.AttributeManager") as mock_attr_manager:
            
            service = DictionaryService(mock_database)
            service.model = mock_model.return_value
            service.attribute_manager = mock_attr_manager.return_value

            # Создание
            service.model.create.return_value = 1
            service.find_dictionary_by_code.return_value = None
            
            dictionary_in = DictionaryIn(
                name="Test Dictionary",
                code="test_001",
                description="Test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                name_eng="Test Dictionary",
                name_bel="Тэставы даведнік",
                description_eng="Test description",
                description_bel="Тэставае апісанне",
                gko="Test GKO",
                organization="Test Org",
                classifier="Test Classifier",
                id_type=1
            )

            # Act & Assert
            # 1. Создание
            created_id = await service.create_dictionary(dictionary_in)
            assert created_id == 1

            # 2. Получение
            service.model.get_dictionary_by_id.return_value = dictionary_in
            retrieved = await service.get_dictionary(1)
            assert retrieved == dictionary_in

            # 3. Обновление
            service.model.update.return_value = True
            updated = await service.update_dictionary(1, dictionary_in)
            assert updated is True

            # 4. Удаление
            service.model.delete.return_value = True
            deleted = await service.delete_dictionary(1)
            assert deleted is True
