"""
Тесты для пользовательских исключений
"""

import pytest
from exceptions import (
    DictionaryNotFoundError,
    DictionaryValidationError,
    DuplicateCodeError,
    FileProcessingError,
    DatabaseConnectionError,
    CacheError
)


class TestDictionaryNotFoundError:
    """Тесты для DictionaryNotFoundError"""

    def test_dictionary_not_found_error_creation(self):
        """Создание исключения DictionaryNotFoundError"""
        # Act
        error = DictionaryNotFoundError(123)

        # Assert
        assert error.dictionary_id == 123
        assert "123" in str(error)
        assert "не найден" in str(error)

    def test_dictionary_not_found_error_message(self):
        """Сообщение об ошибке DictionaryNotFoundError"""
        # Act
        error = DictionaryNotFoundError(999)

        # Assert
        assert "999" in str(error)
        assert "Справочник с ID 999 не найден" in str(error)

    def test_dictionary_not_found_error_inheritance(self):
        """Наследование DictionaryNotFoundError"""
        # Act
        error = DictionaryNotFoundError(1)

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'dictionary_id')


class TestDictionaryValidationError:
    """Тесты для DictionaryValidationError"""

    def test_dictionary_validation_error_creation(self):
        """Создание исключения DictionaryValidationError"""
        # Act
        error = DictionaryValidationError("Invalid data")

        # Assert
        assert error.message == "Invalid data"
        assert "Invalid data" in str(error)

    def test_dictionary_validation_error_default_message(self):
        """Сообщение по умолчанию для DictionaryValidationError"""
        # Act
        error = DictionaryValidationError()

        # Assert
        assert "Ошибка валидации справочника" in str(error)

    def test_dictionary_validation_error_custom_message(self):
        """Пользовательское сообщение для DictionaryValidationError"""
        # Act
        custom_message = "Дата начала должна быть меньше даты окончания"
        error = DictionaryValidationError(custom_message)

        # Assert
        assert error.message == custom_message
        assert custom_message in str(error)

    def test_dictionary_validation_error_inheritance(self):
        """Наследование DictionaryValidationError"""
        # Act
        error = DictionaryValidationError("Test")

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'message')


class TestDuplicateCodeError:
    """Тесты для DuplicateCodeError"""

    def test_duplicate_code_error_creation(self):
        """Создание исключения DuplicateCodeError"""
        # Act
        error = DuplicateCodeError("test_001")

        # Assert
        assert error.code == "test_001"
        assert "test_001" in str(error)
        assert "уже существует" in str(error)

    def test_duplicate_code_error_message(self):
        """Сообщение об ошибке DuplicateCodeError"""
        # Act
        error = DuplicateCodeError("duplicate_code")

        # Assert
        assert "duplicate_code" in str(error)
        assert "Справочник с кодом duplicate_code уже существует" in str(error)

    def test_duplicate_code_error_inheritance(self):
        """Наследование DuplicateCodeError"""
        # Act
        error = DuplicateCodeError("test")

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'code')


class TestFileProcessingError:
    """Тесты для FileProcessingError"""

    def test_file_processing_error_creation(self):
        """Создание исключения FileProcessingError"""
        # Act
        error = FileProcessingError("File processing failed")

        # Assert
        assert error.message == "File processing failed"
        assert "File processing failed" in str(error)

    def test_file_processing_error_default_message(self):
        """Сообщение по умолчанию для FileProcessingError"""
        # Act
        error = FileProcessingError()

        # Assert
        assert "Ошибка обработки файла" in str(error)

    def test_file_processing_error_with_filename(self):
        """FileProcessingError с именем файла"""
        # Act
        error = FileProcessingError("Invalid format", "test.csv")

        # Assert
        assert error.message == "Invalid format"
        assert error.filename == "test.csv"
        assert "test.csv" in str(error)

    def test_file_processing_error_inheritance(self):
        """Наследование FileProcessingError"""
        # Act
        error = FileProcessingError("Test")

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'message')


class TestDatabaseConnectionError:
    """Тесты для DatabaseConnectionError"""

    def test_database_connection_error_creation(self):
        """Создание исключения DatabaseConnectionError"""
        # Act
        error = DatabaseConnectionError("Connection failed")

        # Assert
        assert error.message == "Connection failed"
        assert "Connection failed" in str(error)

    def test_database_connection_error_default_message(self):
        """Сообщение по умолчанию для DatabaseConnectionError"""
        # Act
        error = DatabaseConnectionError()

        # Assert
        assert "Ошибка подключения к базе данных" in str(error)

    def test_database_connection_error_with_details(self):
        """DatabaseConnectionError с деталями"""
        # Act
        error = DatabaseConnectionError("Connection timeout", "PostgreSQL")

        # Assert
        assert error.message == "Connection timeout"
        assert error.database_type == "PostgreSQL"
        assert "PostgreSQL" in str(error)

    def test_database_connection_error_inheritance(self):
        """Наследование DatabaseConnectionError"""
        # Act
        error = DatabaseConnectionError("Test")

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'message')


class TestCacheError:
    """Тесты для CacheError"""

    def test_cache_error_creation(self):
        """Создание исключения CacheError"""
        # Act
        error = CacheError("Cache operation failed")

        # Assert
        assert error.message == "Cache operation failed"
        assert "Cache operation failed" in str(error)

    def test_cache_error_default_message(self):
        """Сообщение по умолчанию для CacheError"""
        # Act
        error = CacheError()

        # Assert
        assert "Ошибка кэширования" in str(error)

    def test_cache_error_with_operation(self):
        """CacheError с операцией"""
        # Act
        error = CacheError("Set operation failed", "set")

        # Assert
        assert error.message == "Set operation failed"
        assert error.operation == "set"
        assert "set" in str(error)

    def test_cache_error_inheritance(self):
        """Наследование CacheError"""
        # Act
        error = CacheError("Test")

        # Assert
        assert isinstance(error, Exception)
        assert hasattr(error, 'message')


class TestExceptionHierarchy:
    """Тесты иерархии исключений"""

    def test_exception_hierarchy(self):
        """Проверка иерархии исключений"""
        # Arrange
        exceptions = [
            DictionaryNotFoundError(1),
            DictionaryValidationError("Test"),
            DuplicateCodeError("test"),
            FileProcessingError("Test"),
            DatabaseConnectionError("Test"),
            CacheError("Test")
        ]

        # Act & Assert
        for exception in exceptions:
            assert isinstance(exception, Exception)
            assert hasattr(exception, '__str__')

    def test_exception_attributes(self):
        """Проверка атрибутов исключений"""
        # Act & Assert
        # DictionaryNotFoundError
        error1 = DictionaryNotFoundError(123)
        assert hasattr(error1, 'dictionary_id')
        assert error1.dictionary_id == 123

        # DictionaryValidationError
        error2 = DictionaryValidationError("Test message")
        assert hasattr(error2, 'message')
        assert error2.message == "Test message"

        # DuplicateCodeError
        error3 = DuplicateCodeError("test_code")
        assert hasattr(error3, 'code')
        assert error3.code == "test_code"

        # FileProcessingError
        error4 = FileProcessingError("Test", "test.csv")
        assert hasattr(error4, 'message')
        assert hasattr(error4, 'filename')
        assert error4.filename == "test.csv"

        # DatabaseConnectionError
        error5 = DatabaseConnectionError("Test", "PostgreSQL")
        assert hasattr(error5, 'message')
        assert hasattr(error5, 'database_type')
        assert error5.database_type == "PostgreSQL"

        # CacheError
        error6 = CacheError("Test", "get")
        assert hasattr(error6, 'message')
        assert hasattr(error6, 'operation')
        assert error6.operation == "get"


class TestExceptionMessages:
    """Тесты сообщений исключений"""

    def test_dictionary_not_found_error_message_format(self):
        """Формат сообщения DictionaryNotFoundError"""
        # Act
        error = DictionaryNotFoundError(999)

        # Assert
        message = str(error)
        assert "999" in message
        assert "не найден" in message
        assert "Справочник с ID" in message

    def test_duplicate_code_error_message_format(self):
        """Формат сообщения DuplicateCodeError"""
        # Act
        error = DuplicateCodeError("duplicate_code")

        # Assert
        message = str(error)
        assert "duplicate_code" in message
        assert "уже существует" in message
        assert "Справочник с кодом" in message

    def test_file_processing_error_message_format(self):
        """Формат сообщения FileProcessingError"""
        # Act
        error = FileProcessingError("Invalid format", "test.csv")

        # Assert
        message = str(error)
        assert "Invalid format" in message
        assert "test.csv" in message

    def test_database_connection_error_message_format(self):
        """Формат сообщения DatabaseConnectionError"""
        # Act
        error = DatabaseConnectionError("Connection timeout", "PostgreSQL")

        # Assert
        message = str(error)
        assert "Connection timeout" in message
        assert "PostgreSQL" in message

    def test_cache_error_message_format(self):
        """Формат сообщения CacheError"""
        # Act
        error = CacheError("Set operation failed", "set")

        # Assert
        message = str(error)
        assert "Set operation failed" in message
        assert "set" in message


class TestExceptionUsage:
    """Тесты использования исключений"""

    def test_exception_raising_and_catching(self):
        """Вызов и перехват исключений"""
        # Act & Assert
        # DictionaryNotFoundError
        with pytest.raises(DictionaryNotFoundError) as exc_info:
            raise DictionaryNotFoundError(123)
        assert exc_info.value.dictionary_id == 123

        # DictionaryValidationError
        with pytest.raises(DictionaryValidationError) as exc_info:
            raise DictionaryValidationError("Invalid data")
        assert exc_info.value.message == "Invalid data"

        # DuplicateCodeError
        with pytest.raises(DuplicateCodeError) as exc_info:
            raise DuplicateCodeError("test_code")
        assert exc_info.value.code == "test_code"

        # FileProcessingError
        with pytest.raises(FileProcessingError) as exc_info:
            raise FileProcessingError("File error", "test.csv")
        assert exc_info.value.filename == "test.csv"

        # DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError) as exc_info:
            raise DatabaseConnectionError("DB error", "PostgreSQL")
        assert exc_info.value.database_type == "PostgreSQL"

        # CacheError
        with pytest.raises(CacheError) as exc_info:
            raise CacheError("Cache error", "get")
        assert exc_info.value.operation == "get"

    def test_exception_inheritance_chain(self):
        """Цепочка наследования исключений"""
        # Act & Assert
        error = DictionaryNotFoundError(1)
        
        # Проверяем, что исключение является экземпляром базовых классов
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)

    def test_exception_serialization(self):
        """Сериализация исключений"""
        # Arrange
        error = DictionaryNotFoundError(123)

        # Act
        error_dict = {
            'type': type(error).__name__,
            'dictionary_id': error.dictionary_id,
            'message': str(error)
        }

        # Assert
        assert error_dict['type'] == 'DictionaryNotFoundError'
        assert error_dict['dictionary_id'] == 123
        assert '123' in error_dict['message']
