"""
Тесты для модуля model_attribute.py

Покрывает все основные методы класса AttributeManager:
- Создание и импорт данных
- Работу с временными периодами
- Управление иерархией
- Обработку ошибок
"""

import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from models.model_attribute import AttributeManager
from schemas import AttrShown


class TestAttributeManager:
    """Тесты для класса AttributeManager"""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Тестовый DataFrame для импорта"""
        return pd.DataFrame(
            {
                "CODE": ["001", "002", "003"],
                "NAME": ["Item 1", "Item 2", "Item 3"],
                "PARENT_CODE": ["", "001", "001"],
                "DESCRIPTION": ["Desc 1", "Desc 2", "Desc 3"],
            }
        )

    @pytest.fixture
    def sample_attrs_list(self) -> List[AttrShown]:
        """Тестовый список атрибутов"""
        return [
            AttrShown(name="CODE", value="001"),
            AttrShown(name="NAME", value="Test Item"),
            AttrShown(name="START_DATE", value="2024-01-01"),
            AttrShown(name="FINISH_DATE", value="2024-12-31"),
            AttrShown(name="DESCRIPTION", value="Test description"),
        ]

    @pytest.fixture
    def mock_database(self):
        """Мок для базы данных"""
        with patch("model_attribute.database") as mock_db:
            yield mock_db

    class TestFetchDates:
        """Тесты для метода _fetch_dates"""

        @pytest.mark.asyncio
        async def test_fetch_dates_success(self, mock_database):
            # Arrange
            dictionary_id = 1
            expected_dates = {
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 12, 31),
            }
            mock_database.fetch_one.return_value = expected_dates

            # Act
            result = await AttributeManager._fetch_dates(dictionary_id)

            # Assert
            assert result == expected_dates
            mock_database.fetch_one.assert_called_once_with(
                "SELECT start_date, finish_date FROM dictionary WHERE id = :id",
                {"id": dictionary_id},
            )

        @pytest.mark.asyncio
        async def test_fetch_dates_not_found(self, mock_database):
            # Arrange
            mock_database.fetch_one.return_value = None

            # Act & Assert
            with pytest.raises(TypeError):
                await AttributeManager._fetch_dates(999)

    class TestBatchCreatePositions:
        """Тесты для создания позиций"""

        @pytest.mark.asyncio
        async def test_batch_create_positions_success(self, mock_database):
            # Arrange
            dictionary_id = 1
            count = 3
            expected_ids = [1, 2, 3]
            mock_database.fetch_all.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]

            # Act
            result = await AttributeManager._batch_create_positions(
                dictionary_id, count
            )

            # Assert
            assert result == expected_ids
            mock_database.fetch_all.assert_called_once()

        @pytest.mark.asyncio
        async def test_single_create_positions_success(self, mock_database):
            # Arrange
            dictionary_id = 1
            expected_id = 1
            mock_database.fetch_one.return_value = {"id": expected_id}

            # Act
            result = await AttributeManager._single_create_positions(dictionary_id)

            # Assert
            assert result == expected_id
            mock_database.fetch_one.assert_called_once()

    class TestGetAttributesInfo:
        """Тесты для получения информации об атрибутах"""

        @pytest.mark.asyncio
        async def test_get_attributes_info_success(self, mock_database):
            # Arrange
            dictionary_id = 1
            mock_database.fetch_all.return_value = [
                {"id": 1, "alt_name": "CODE"},
                {"id": 2, "alt_name": "NAME"},
                {"id": 3, "alt_name": "DESCRIPTION"},
            ]

            # Act
            result = await AttributeManager._get_attributes_info(dictionary_id)

            # Assert
            expected = {"CODE": {"id": 1}, "NAME": {"id": 2}, "DESCRIPTION": {"id": 3}}
            assert result == expected

        @pytest.mark.asyncio
        async def test_get_attributes_info_empty(self, mock_database):
            # Arrange
            mock_database.fetch_all.return_value = []

            # Act
            result = await AttributeManager._get_attributes_info(1)

            # Assert
            assert result == {}

    class TestImportData:
        """Тесты для импорта данных"""

        @pytest.mark.asyncio
        async def test_import_data_success(self, mock_database, sample_dataframe):
            # Arrange
            dictionary_id = 1
            mock_database.fetch_one.return_value = {
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 12, 31),
            }
            mock_database.fetch_all.side_effect = [
                [{"id": 1, "alt_name": "CODE"}, {"id": 2, "alt_name": "NAME"}],
                [{"id": 1}, {"id": 2}, {"id": 3}],  # positions
            ]
            mock_database.execute_many = AsyncMock()

            with patch.object(
                AttributeManager, "generate_relations_for_dictionary"
            ) as mock_relations:
                # Act
                await AttributeManager.import_data(dictionary_id, sample_dataframe)

                # Assert
                mock_database.execute_many.assert_called()
                mock_relations.assert_called_once_with(dictionary_id)

        @pytest.mark.asyncio
        async def test_import_data_missing_columns(self, mock_database):
            # Arrange
            invalid_df = pd.DataFrame({"INVALID": ["test"]})

            # Act & Assert
            with pytest.raises(
                ValueError, match="DataFrame must contain CODE and NAME columns"
            ):
                await AttributeManager.import_data(1, invalid_df)

        @pytest.mark.asyncio
        async def test_import_data_empty_dataframe(self, mock_database):
            # Arrange
            empty_df = pd.DataFrame({"CODE": [], "NAME": []})
            mock_database.fetch_one.return_value = {
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 12, 31),
            }
            mock_database.fetch_all.return_value = []

            with patch.object(
                AttributeManager, "_batch_create_positions"
            ) as mock_create:
                mock_create.return_value = []

                # Act
                await AttributeManager.import_data(1, empty_df)

                # Assert
                mock_create.assert_called_once_with(1, 0)

    class TestCreatePosition:
        """Тесты для создания позиции"""

        @pytest.mark.asyncio
        async def test_create_position_success(self, mock_database, sample_attrs_list):
            # Arrange
            dictionary_id = 1
            position_id = 1

            mock_database.fetch_all.return_value = [
                {"alt_name": "CODE"},
                {"alt_name": "NAME"},
            ]
            mock_database.fetch_one.return_value = {"id": position_id}

            with patch.object(AttributeManager, "_get_attributes_info") as mock_attrs:
                mock_attrs.return_value = {
                    "CODE": {"id": 1},
                    "NAME": {"id": 2},
                    "DESCRIPTION": {"id": 3},
                }

                with patch.object(
                    AttributeManager, "_batch_insert_data"
                ) as mock_insert:
                    with patch.object(
                        AttributeManager, "_update_position_relations"
                    ) as mock_relations:
                        # Act
                        await AttributeManager.create_position(
                            dictionary_id, sample_attrs_list
                        )

                        # Assert
                        mock_insert.assert_called_once()
                        mock_relations.assert_called_once_with(
                            position_id, dictionary_id
                        )

        @pytest.mark.asyncio
        async def test_create_position_empty_data(self, mock_database):
            # Arrange
            empty_attrs = []

            # Act & Assert
            with pytest.raises(ValueError, match="Empty data provided"):
                await AttributeManager.create_position(1, empty_attrs)

        @pytest.mark.asyncio
        async def test_create_position_missing_required_fields(self, mock_database):
            # Arrange
            attrs_list = [AttrShown(name="CODE", value="001")]

            with patch.object(
                AttributeManager, "_get_required_fields"
            ) as mock_required:
                mock_required.return_value = ["CODE", "NAME", "MANDATORY_FIELD"]

                # Act & Assert
                with pytest.raises(ValueError, match="Missing required fields"):
                    await AttributeManager.create_position(1, attrs_list)

    class TestEditPosition:
        """Тесты для редактирования позиции"""

        @pytest.mark.asyncio
        async def test_edit_position_success(self, mock_database, sample_attrs_list):
            # Arrange
            position_id = 1
            dictionary_id = 1

            mock_database.fetch_one.return_value = {"id_dictionary": dictionary_id}

            with patch.object(AttributeManager, "_get_attributes_info") as mock_attrs:
                mock_attrs.return_value = {"CODE": {"id": 1}, "NAME": {"id": 2}}

                with patch.object(
                    AttributeManager, "_delete_nested_period"
                ) as mock_delete:
                    with patch.object(
                        AttributeManager, "_shift_next_period"
                    ) as mock_next:
                        with patch.object(
                            AttributeManager, "_shift_previous_period"
                        ) as mock_prev:
                            with patch.object(
                                AttributeManager, "_insert_position"
                            ) as mock_insert:
                                with patch.object(
                                    AttributeManager, "_update_position_relations"
                                ) as mock_relations:
                                    mock_next.return_value = date(2024, 12, 31)
                                    mock_prev.return_value = date(2024, 1, 1)

                                    # Act
                                    await AttributeManager.edit_position(
                                        position_id, sample_attrs_list
                                    )

                                    # Assert
                                    mock_delete.assert_called()
                                    mock_next.assert_called()
                                    mock_prev.assert_called()
                                    mock_insert.assert_called()
                                    mock_relations.assert_called_once()

    class TestDeleteNestedPeriod:
        """Тесты для удаления вложенных периодов"""

        @pytest.mark.asyncio
        async def test_delete_nested_period_success(self, mock_database):
            # Arrange
            position_id = 1
            attribute_id = 1
            start_date = date(2024, 1, 1)
            finish_date = date(2024, 12, 31)

            mock_database.execute = AsyncMock()

            # Act
            await AttributeManager._delete_nested_period(
                position_id, attribute_id, start_date, finish_date
            )

            # Assert
            mock_database.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_delete_nested_period_invalid_dates(self, mock_database):
            # Arrange
            start_date = date(2024, 12, 31)
            finish_date = date(2024, 1, 1)  # Неверный порядок дат

            # Act & Assert
            with pytest.raises(
                ValueError, match="Start date cannot be after finish date"
            ):
                await AttributeManager._delete_nested_period(
                    1, 1, start_date, finish_date
                )

    class TestShiftPeriods:
        """Тесты для сдвига периодов"""

        @pytest.mark.asyncio
        async def test_shift_next_period_different_values(self, mock_database):
            # Arrange
            position_id = 1
            attribute_id = 1
            finish_date = date(2024, 6, 30)
            value = "test_value"

            mock_database.fetch_one.return_value = {
                "id": 1,
                "value": "different_value",
                "finish_date": date(2024, 12, 31),
            }
            mock_database.execute = AsyncMock()

            # Act
            result = await AttributeManager._shift_next_period(
                position_id, attribute_id, finish_date, value
            )

            # Assert
            assert result == finish_date
            mock_database.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_shift_next_period_same_values(self, mock_database):
            # Arrange
            position_id = 1
            attribute_id = 1
            finish_date = date(2024, 6, 30)
            value = "same_value"

            mock_database.fetch_one.return_value = {
                "id": 1,
                "value": "same_value",
                "finish_date": date(2024, 12, 31),
            }
            mock_database.execute = AsyncMock()

            # Act
            result = await AttributeManager._shift_next_period(
                position_id, attribute_id, finish_date, value
            )

            # Assert
            assert result == date(2024, 12, 31)
            mock_database.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_shift_next_period_no_next_period(self, mock_database):
            # Arrange
            mock_database.fetch_one.return_value = None
            finish_date = date(2024, 6, 30)

            # Act
            result = await AttributeManager._shift_next_period(
                1, 1, finish_date, "value"
            )

            # Assert
            assert result == finish_date

        @pytest.mark.asyncio
        async def test_shift_previous_period_same_values(self, mock_database):
            # Arrange
            position_id = 1
            attribute_id = 1
            start_date = date(2024, 6, 1)
            value = "same_value"

            mock_database.fetch_one.return_value = {
                "id": 1,
                "value": "same_value",
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 5, 31),
            }
            mock_database.execute = AsyncMock()

            # Act
            result = await AttributeManager._shift_previous_period(
                position_id, attribute_id, start_date, value
            )

            # Assert
            assert result == date(2024, 1, 1)
            mock_database.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_shift_previous_period_different_values(self, mock_database):
            # Arrange
            position_id = 1
            attribute_id = 1
            start_date = date(2024, 6, 1)
            value = "new_value"

            mock_database.fetch_one.return_value = {
                "id": 1,
                "value": "old_value",
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 5, 31),
            }
            mock_database.execute = AsyncMock()

            # Act
            result = await AttributeManager._shift_previous_period(
                position_id, attribute_id, start_date, value
            )

            # Assert
            assert result == start_date
            mock_database.execute.assert_called_once()

    class TestUpdatePositionRelations:
        """Тесты для обновления отношений позиций"""

        @pytest.mark.asyncio
        async def test_update_position_relations_success(self, mock_database):
            # Arrange
            position_id = 1
            dictionary_id = 1

            mock_database.execute = AsyncMock()
            mock_database.fetch_all.side_effect = [
                # parent_codes
                [
                    {
                        "value": "PARENT_001",
                        "start_date": date(2024, 1, 1),
                        "finish_date": date(2024, 12, 31),
                    }
                ],
                # candidates
                [
                    {
                        "id_position": 2,
                        "start_date": date(2024, 1, 1),
                        "finish_date": date(2024, 12, 31),
                    }
                ],
            ]
            mock_database.execute_many = AsyncMock()

            # Act
            await AttributeManager._update_position_relations(
                position_id, dictionary_id
            )

            # Assert
            mock_database.execute.assert_called()  # DELETE запрос
            mock_database.execute_many.assert_called()  # INSERT запрос

        @pytest.mark.asyncio
        async def test_update_position_relations_no_overlapping_dates(
            self, mock_database
        ):
            # Arrange
            position_id = 1
            dictionary_id = 1

            mock_database.execute = AsyncMock()
            mock_database.fetch_all.side_effect = [
                # parent_codes
                [
                    {
                        "value": "PARENT_001",
                        "start_date": date(2024, 1, 1),
                        "finish_date": date(2024, 6, 30),
                    }
                ],
                # candidates (не пересекающиеся даты)
                [
                    {
                        "id_position": 2,
                        "start_date": date(2024, 7, 1),
                        "finish_date": date(2024, 12, 31),
                    }
                ],
            ]
            mock_database.execute_many = AsyncMock()

            # Act
            await AttributeManager._update_position_relations(
                position_id, dictionary_id
            )

            # Assert
            mock_database.execute_many.assert_not_called()

    class TestGenerateRelationsForDictionary:
        """Тесты для генерации отношений справочника"""

        @pytest.mark.asyncio
        async def test_generate_relations_for_dictionary_success(self, mock_database):
            # Arrange
            dictionary_id = 1
            mock_database.fetch_all.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]

            with patch.object(
                AttributeManager, "_update_position_relations"
            ) as mock_update:
                with patch("asyncio.gather") as mock_gather:
                    # Act
                    await AttributeManager.generate_relations_for_dictionary(
                        dictionary_id
                    )

                    # Assert
                    mock_gather.assert_called_once()
                    assert mock_update.call_count == 0  # Вызывается через gather

    class TestHelperMethods:
        """Тесты для вспомогательных методов"""

        @pytest.mark.asyncio
        async def test_get_dictionary_by_position(self, mock_database):
            # Arrange
            position_id = 1
            expected_dict_id = 5
            mock_database.fetch_one.return_value = {"id_dictionary": expected_dict_id}

            # Act
            result = await AttributeManager._get_dictionary_by_position(position_id)

            # Assert
            assert result == expected_dict_id

        @pytest.mark.asyncio
        async def test_get_required_fields(self, mock_database):
            # Arrange
            dictionary_id = 1
            mock_database.fetch_all.return_value = [
                {"alt_name": "CODE"},
                {"alt_name": "NAME"},
                {"alt_name": "MANDATORY_FIELD"},
            ]

            # Act
            result = await AttributeManager._get_required_fields(dictionary_id)

            # Assert
            expected = ["CODE", "NAME", "MANDATORY_FIELD"]
            assert result == expected

        @pytest.mark.asyncio
        async def test_batch_insert_data(self, mock_database):
            # Arrange
            data = [
                {
                    "id_position": 1,
                    "id_attribute": 1,
                    "start_date": date(2024, 1, 1),
                    "finish_date": date(2024, 12, 31),
                    "value": "test_value",
                }
            ]
            mock_database.execute_many = AsyncMock()

            # Act
            await AttributeManager._batch_insert_data(data)

            # Assert
            mock_database.execute_many.assert_called_once()

        @pytest.mark.asyncio
        async def test_insert_position(self, mock_database):
            # Arrange
            data = {
                "id_position": 1,
                "id_attribute": 1,
                "start_date": date(2024, 1, 1),
                "finish_date": date(2024, 12, 31),
                "value": "test_value",
            }
            mock_database.execute = AsyncMock()

            # Act
            await AttributeManager._insert_position(data)

            # Assert
            mock_database.execute.assert_called_once()

    class TestConstants:
        """Тесты для констант класса"""

        def test_null_values_constant(self):
            # Act & Assert
            assert AttributeManager.NULL_VALUES == ("nan", "none", "null", "")

        def test_batch_size_constant(self):
            # Act & Assert
            assert AttributeManager.BATCH_SIZE == 1000

    class TestErrorHandling:
        """Тесты для обработки ошибок"""

        @pytest.mark.asyncio
        async def test_create_position_database_error(
            self, mock_database, sample_attrs_list
        ):
            # Arrange
            mock_database.fetch_all.side_effect = Exception("Database connection error")

            # Act & Assert
            with pytest.raises(Exception, match="Position creation failed"):
                await AttributeManager.create_position(1, sample_attrs_list)

        @pytest.mark.asyncio
        async def test_edit_position_database_error(
            self, mock_database, sample_attrs_list
        ):
            # Arrange
            mock_database.fetch_one.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(Exception, match="Position creation failed"):
                await AttributeManager.edit_position(1, sample_attrs_list)

        @pytest.mark.asyncio
        async def test_delete_nested_period_database_error(self, mock_database):
            # Arrange
            mock_database.execute.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(Exception):
                await AttributeManager._delete_nested_period(
                    1, 1, date(2024, 1, 1), date(2024, 12, 31)
                )


# Интеграционные тесты
class TestAttributeManagerIntegration:
    """Интеграционные тесты для проверки взаимодействия методов"""

    @pytest.mark.asyncio
    async def test_full_import_workflow(self, mock_database):
        # Arrange
        dictionary_id = 1
        df = pd.DataFrame(
            {
                "CODE": ["001", "002"],
                "NAME": ["Item 1", "Item 2"],
                "PARENT_CODE": ["", "001"],
            }
        )

        mock_database.fetch_one.return_value = {
            "start_date": date(2024, 1, 1),
            "finish_date": date(2024, 12, 31),
        }
        mock_database.fetch_all.side_effect = [
            [{"id": 1, "alt_name": "CODE"}, {"id": 2, "alt_name": "NAME"}],
            [{"id": 1}, {"id": 2}],  # positions
            [{"id": 1}, {"id": 2}],  # для generate_relations
        ]
        mock_database.execute_many = AsyncMock()
        mock_database.execute = AsyncMock()

        with patch("asyncio.gather") as mock_gather:
            # Act
            await AttributeManager.import_data(dictionary_id, df)

            # Assert
            mock_database.execute_many.assert_called()
            mock_gather.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_edit_position_workflow(self, mock_database):
        # Arrange
        dictionary_id = 1
        position_id = 1
        attrs_list = [
            AttrShown(name="CODE", value="001"),
            AttrShown(name="NAME", value="Test Item"),
            AttrShown(name="START_DATE", value="2024-01-01"),
            AttrShown(name="FINISH_DATE", value="2024-12-31"),
        ]

        # Моки для create_position
        mock_database.fetch_all.return_value = [{"alt_name": "CODE"}]
        mock_database.fetch_one.side_effect = [
            {"id": position_id},  # create position
            {"id_dictionary": dictionary_id},  # get dictionary by position
        ]

        with patch.object(AttributeManager, "_get_attributes_info") as mock_attrs:
            mock_attrs.return_value = {"CODE": {"id": 1}, "NAME": {"id": 2}}

            with patch.object(AttributeManager, "_batch_insert_data") as mock_insert:
                with patch.object(
                    AttributeManager, "_update_position_relations"
                ) as mock_relations:
                    with patch.object(
                        AttributeManager, "_delete_nested_period"
                    ) as mock_delete:
                        with patch.object(
                            AttributeManager, "_shift_next_period"
                        ) as mock_next:
                            with patch.object(
                                AttributeManager, "_shift_previous_period"
                            ) as mock_prev:
                                with patch.object(
                                    AttributeManager, "_insert_position"
                                ) as mock_insert_pos:
                                    mock_next.return_value = date(2024, 12, 31)
                                    mock_prev.return_value = date(2024, 1, 1)

                                    # Act
                                    await AttributeManager.create_position(
                                        dictionary_id, attrs_list
                                    )
                                    await AttributeManager.edit_position(
                                        position_id, attrs_list
                                    )

                                    # Assert
                                    assert mock_relations.call_count == 2
                                    mock_insert.assert_called_once()
                                    mock_insert_pos.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
