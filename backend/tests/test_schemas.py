"""
Тесты для схем данных Pydantic
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from schemas import (
    DictionaryIn, DictionaryOut, DictionaryPosition, 
    AttributeDict, AttrShown, DictionaryType
)


class TestDictionaryIn:
    """Тесты для схемы DictionaryIn"""

    @pytest.fixture
    def valid_dictionary_data(self):
        """Валидные данные для создания справочника"""
        return {
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "name_eng": "Test Dictionary",
            "name_bel": "Тэставы даведнік",
            "description_eng": "Test description",
            "description_bel": "Тэставае апісанне",
            "gko": "Test GKO",
            "organization": "Test Org",
            "classifier": "Test Classifier",
            "id_type": 1
        }

    def test_valid_dictionary_in(self, valid_dictionary_data):
        """Создание валидного DictionaryIn"""
        # Act
        dictionary = DictionaryIn(**valid_dictionary_data)

        # Assert
        assert dictionary.name == "Test Dictionary"
        assert dictionary.code == "test_001"
        assert dictionary.start_date == date(2024, 1, 1)
        assert dictionary.finish_date == date(2024, 12, 31)
        assert dictionary.id_type == 1

    def test_dictionary_in_missing_required_fields(self, valid_dictionary_data):
        """Отсутствие обязательных полей"""
        # Arrange
        del valid_dictionary_data["name"]

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)

    def test_dictionary_in_invalid_dates(self, valid_dictionary_data):
        """Некорректные даты"""
        # Arrange
        valid_dictionary_data["start_date"] = "2024-12-31"
        valid_dictionary_data["finish_date"] = "2024-01-01"

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)

    def test_dictionary_in_invalid_date_format(self, valid_dictionary_data):
        """Некорректный формат даты"""
        # Arrange
        valid_dictionary_data["start_date"] = "invalid-date"

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)

    def test_dictionary_in_empty_strings(self, valid_dictionary_data):
        """Пустые строки в обязательных полях"""
        # Arrange
        valid_dictionary_data["name"] = ""

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)

    def test_dictionary_in_optional_fields(self, valid_dictionary_data):
        """Опциональные поля"""
        # Arrange
        del valid_dictionary_data["name_eng"]
        del valid_dictionary_data["name_bel"]

        # Act
        dictionary = DictionaryIn(**valid_dictionary_data)

        # Assert
        assert dictionary.name_eng is None
        assert dictionary.name_bel is None

    def test_dictionary_in_string_length_validation(self, valid_dictionary_data):
        """Валидация длины строк"""
        # Arrange
        valid_dictionary_data["name"] = "x" * 1000  # Слишком длинное имя

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)

    def test_dictionary_in_code_format(self, valid_dictionary_data):
        """Формат кода справочника"""
        # Arrange
        valid_dictionary_data["code"] = "invalid code with spaces"

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryIn(**valid_dictionary_data)


class TestDictionaryOut:
    """Тесты для схемы DictionaryOut"""

    @pytest.fixture
    def valid_dictionary_out_data(self):
        """Валидные данные для DictionaryOut"""
        return {
            "id": 1,
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "name_eng": "Test Dictionary",
            "name_bel": "Тэставы даведнік",
            "description_eng": "Test description",
            "description_bel": "Тэставае апісанне",
            "gko": "Test GKO",
            "organization": "Test Org",
            "classifier": "Test Classifier",
            "id_type": 1,
            "id_status": 1,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }

    def test_valid_dictionary_out(self, valid_dictionary_out_data):
        """Создание валидного DictionaryOut"""
        # Act
        dictionary = DictionaryOut(**valid_dictionary_out_data)

        # Assert
        assert dictionary.id == 1
        assert dictionary.name == "Test Dictionary"
        assert dictionary.created_at == datetime(2024, 1, 1, 10, 0, 0)
        assert dictionary.updated_at == datetime(2024, 1, 1, 10, 0, 0)

    def test_dictionary_out_serialization(self, valid_dictionary_out_data):
        """Сериализация DictionaryOut"""
        # Arrange
        dictionary = DictionaryOut(**valid_dictionary_out_data)

        # Act
        dict_data = dictionary.dict()

        # Assert
        assert isinstance(dict_data, dict)
        assert dict_data["id"] == 1
        assert dict_data["name"] == "Test Dictionary"

    def test_dictionary_out_json_serialization(self, valid_dictionary_out_data):
        """JSON сериализация DictionaryOut"""
        # Arrange
        dictionary = DictionaryOut(**valid_dictionary_out_data)

        # Act
        json_data = dictionary.json()

        # Assert
        assert isinstance(json_data, str)
        assert "Test Dictionary" in json_data


class TestDictionaryPosition:
    """Тесты для схемы DictionaryPosition"""

    @pytest.fixture
    def valid_position_data(self):
        """Валидные данные для позиции справочника"""
        return {
            "id": 1,
            "code": "A1",
            "name": "Test Position",
            "description": "Test position description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "parent_id": None,
            "dictionary_id": 1
        }

    def test_valid_dictionary_position(self, valid_position_data):
        """Создание валидной DictionaryPosition"""
        # Act
        position = DictionaryPosition(**valid_position_data)

        # Assert
        assert position.id == 1
        assert position.code == "A1"
        assert position.name == "Test Position"
        assert position.start_date == date(2024, 1, 1)
        assert position.finish_date == date(2024, 12, 31)

    def test_dictionary_position_with_parent(self, valid_position_data):
        """Позиция с родительским элементом"""
        # Arrange
        valid_position_data["parent_id"] = 5

        # Act
        position = DictionaryPosition(**valid_position_data)

        # Assert
        assert position.parent_id == 5

    def test_dictionary_position_invalid_dates(self, valid_position_data):
        """Некорректные даты в позиции"""
        # Arrange
        valid_position_data["start_date"] = "2024-12-31"
        valid_position_data["finish_date"] = "2024-01-01"

        # Act & Assert
        with pytest.raises(ValidationError):
            DictionaryPosition(**valid_position_data)


class TestAttributeDict:
    """Тесты для схемы AttributeDict"""

    @pytest.fixture
    def valid_attribute_data(self):
        """Валидные данные для атрибута"""
        return {
            "id": 1,
            "name": "CODE",
            "type": "string",
            "required": True,
            "description": "Code attribute"
        }

    def test_valid_attribute_dict(self, valid_attribute_data):
        """Создание валидного AttributeDict"""
        # Act
        attribute = AttributeDict(**valid_attribute_data)

        # Assert
        assert attribute.id == 1
        assert attribute.name == "CODE"
        assert attribute.type == "string"
        assert attribute.required is True

    def test_attribute_dict_optional_fields(self, valid_attribute_data):
        """Опциональные поля в AttributeDict"""
        # Arrange
        del valid_attribute_data["description"]

        # Act
        attribute = AttributeDict(**valid_attribute_data)

        # Assert
        assert attribute.description is None

    def test_attribute_dict_invalid_type(self, valid_attribute_data):
        """Некорректный тип атрибута"""
        # Arrange
        valid_attribute_data["type"] = "invalid_type"

        # Act & Assert
        with pytest.raises(ValidationError):
            AttributeDict(**valid_attribute_data)


class TestAttrShown:
    """Тесты для схемы AttrShown"""

    @pytest.fixture
    def valid_attr_shown_data(self):
        """Валидные данные для AttrShown"""
        return {
            "name": "CODE",
            "value": "A1"
        }

    def test_valid_attr_shown(self, valid_attr_shown_data):
        """Создание валидного AttrShown"""
        # Act
        attr = AttrShown(**valid_attr_shown_data)

        # Assert
        assert attr.name == "CODE"
        assert attr.value == "A1"

    def test_attr_shown_empty_value(self, valid_attr_shown_data):
        """Пустое значение в AttrShown"""
        # Arrange
        valid_attr_shown_data["value"] = ""

        # Act
        attr = AttrShown(**valid_attr_shown_data)

        # Assert
        assert attr.value == ""

    def test_attr_shown_none_value(self, valid_attr_shown_data):
        """None значение в AttrShown"""
        # Arrange
        valid_attr_shown_data["value"] = None

        # Act
        attr = AttrShown(**valid_attr_shown_data)

        # Assert
        assert attr.value is None


class TestDictionaryType:
    """Тесты для схемы DictionaryType"""

    @pytest.fixture
    def valid_type_data(self):
        """Валидные данные для типа справочника"""
        return {
            "id": 1,
            "name": "Test Type",
            "description": "Test type description"
        }

    def test_valid_dictionary_type(self, valid_type_data):
        """Создание валидного DictionaryType"""
        # Act
        dict_type = DictionaryType(**valid_type_data)

        # Assert
        assert dict_type.id == 1
        assert dict_type.name == "Test Type"
        assert dict_type.description == "Test type description"


class TestSchemaValidation:
    """Тесты валидации схем"""

    def test_dictionary_in_date_range_validation(self):
        """Валидация диапазона дат в DictionaryIn"""
        # Arrange
        data = {
            "name": "Test",
            "code": "test_001",
            "description": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**data)

        # Assert
        assert dictionary.start_date < dictionary.finish_date

    def test_dictionary_position_date_validation(self):
        """Валидация дат в DictionaryPosition"""
        # Arrange
        data = {
            "id": 1,
            "code": "A1",
            "name": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "dictionary_id": 1
        }

        # Act
        position = DictionaryPosition(**data)

        # Assert
        assert position.start_date <= position.finish_date

    def test_string_field_validation(self):
        """Валидация строковых полей"""
        # Arrange
        data = {
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**data)

        # Assert
        assert isinstance(dictionary.name, str)
        assert isinstance(dictionary.code, str)
        assert isinstance(dictionary.description, str)

    def test_integer_field_validation(self):
        """Валидация целочисленных полей"""
        # Arrange
        data = {
            "name": "Test",
            "code": "test_001",
            "description": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**data)

        # Assert
        assert isinstance(dictionary.id_type, int)

    def test_date_field_validation(self):
        """Валидация полей даты"""
        # Arrange
        data = {
            "name": "Test",
            "code": "test_001",
            "description": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**data)

        # Assert
        assert isinstance(dictionary.start_date, date)
        assert isinstance(dictionary.finish_date, date)


class TestSchemaSerialization:
    """Тесты сериализации схем"""

    def test_dictionary_in_serialization(self):
        """Сериализация DictionaryIn"""
        # Arrange
        data = {
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }
        dictionary = DictionaryIn(**data)

        # Act
        serialized = dictionary.dict()

        # Assert
        assert isinstance(serialized, dict)
        assert serialized["name"] == "Test Dictionary"
        assert serialized["code"] == "test_001"

    def test_dictionary_out_serialization(self):
        """Сериализация DictionaryOut"""
        # Arrange
        data = {
            "id": 1,
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1,
            "id_status": 1,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
        dictionary = DictionaryOut(**data)

        # Act
        serialized = dictionary.dict()

        # Assert
        assert isinstance(serialized, dict)
        assert serialized["id"] == 1
        assert serialized["name"] == "Test Dictionary"

    def test_json_serialization(self):
        """JSON сериализация"""
        # Arrange
        data = {
            "name": "Test Dictionary",
            "code": "test_001",
            "description": "Test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }
        dictionary = DictionaryIn(**data)

        # Act
        json_str = dictionary.json()

        # Assert
        assert isinstance(json_str, str)
        assert "Test Dictionary" in json_str
        assert "test_001" in json_str


class TestSchemaEdgeCases:
    """Тесты граничных случаев схем"""

    def test_dictionary_in_minimal_data(self):
        """Минимальные данные для DictionaryIn"""
        # Arrange
        minimal_data = {
            "name": "Test",
            "code": "test_001",
            "description": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**minimal_data)

        # Assert
        assert dictionary.name == "Test"
        assert dictionary.name_eng is None
        assert dictionary.name_bel is None

    def test_dictionary_position_same_dates(self):
        """Позиция с одинаковыми датами начала и окончания"""
        # Arrange
        data = {
            "id": 1,
            "code": "A1",
            "name": "Test",
            "start_date": "2024-01-01",
            "finish_date": "2024-01-01",
            "dictionary_id": 1
        }

        # Act
        position = DictionaryPosition(**data)

        # Assert
        assert position.start_date == position.finish_date

    def test_attribute_dict_all_types(self):
        """Все типы атрибутов"""
        valid_types = ["string", "integer", "float", "boolean", "date"]
        
        for attr_type in valid_types:
            data = {
                "id": 1,
                "name": "TEST",
                "type": attr_type,
                "required": True
            }
            
            # Act
            attribute = AttributeDict(**data)
            
            # Assert
            assert attribute.type == attr_type

    def test_attr_shown_special_characters(self):
        """Специальные символы в AttrShown"""
        # Arrange
        data = {
            "name": "SPECIAL_CHAR",
            "value": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        }

        # Act
        attr = AttrShown(**data)

        # Assert
        assert attr.name == "SPECIAL_CHAR"
        assert attr.value == "!@#$%^&*()_+-=[]{}|;':\",./<>?"

    def test_dictionary_in_unicode_support(self):
        """Поддержка Unicode в DictionaryIn"""
        # Arrange
        data = {
            "name": "Тестовый справочник",
            "code": "test_001",
            "description": "Описание с кириллицей",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "name_eng": "Test Dictionary",
            "name_bel": "Тэставы даведнік",
            "description_eng": "Test description",
            "description_bel": "Тэставае апісанне",
            "gko": "Test GKO",
            "organization": "Test Org",
            "classifier": "Test Classifier",
            "id_type": 1
        }

        # Act
        dictionary = DictionaryIn(**data)

        # Assert
        assert dictionary.name == "Тестовый справочник"
        assert dictionary.description == "Описание с кириллицей"
        assert dictionary.name_bel == "Тэставы даведнік"
        assert dictionary.description_bel == "Тэставае апісанне"
