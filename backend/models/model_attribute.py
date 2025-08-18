"""
Модуль для управления атрибутами справочников с поддержкой временных периодов

Особенности:
- Пакетная обработка данных
- Оптимизированные SQL-запросы
- Поддержка временных периодов
- Полноценное логирование

"""
# pylint: disable=import-error
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd

from config import settings
from database import database
from schemas import AttrShown

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT,
    handlers=[logging.FileHandler(settings.LOG_FILE), logging.StreamHandler()],
)

logging.getLogger("databases").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


class AttributeManager:
    """
    Класс для работы с атрибутами справочников
    """

    # Константы
    NULL_VALUES = ("nan", "none", "null", "")
    BATCH_SIZE = 1000

    @staticmethod
    async def _fetch_dates(dictionary_id: int) -> Dict[str, datetime.date]:
        """Получаем сразу все даты для справочника одним запросом"""
        sql = "SELECT start_date, finish_date FROM dictionary WHERE id = :id"
        row = await database.fetch_one(sql, {"id": dictionary_id})
        return {"start_date": row["start_date"], "finish_date": row["finish_date"]}

    @staticmethod
    async def _batch_create_positions(dictionary_id: int, count: int) -> List[int]:
        """Создаем несколько позиций одним запросом"""
        sql = """
            INSERT INTO dictionary_positions (id_dictionary)
            SELECT :id_dictionary FROM generate_series(1, :count)
            RETURNING id
        """
        rows = await database.fetch_all(
            sql, {"id_dictionary": dictionary_id, "count": count}
        )
        return [row["id"] for row in rows]

    @staticmethod
    async def _single_create_positions(dictionary_id: int) -> List[int]:
        """Создаем одну позицию одним запросом"""
        sql = """
            INSERT INTO dictionary_positions (id_dictionary)
            values (:id_dictionary)
            RETURNING id
        """
        row = await database.fetch_one(sql, {"id_dictionary": dictionary_id})
        return row["id"]

    @staticmethod
    async def _get_attributes_info(dictionary_id: int) -> Dict[str, Dict]:
        """Получаем всю информацию об атрибутах одним запросом"""
        sql = """
                SELECT id, alt_name FROM dictionary_attribute
                WHERE id_dictionary = :id_dictionary AND alt_name IS NOT NULL
            """
        rows = await database.fetch_all(sql, {"id_dictionary": dictionary_id})
        return {row["alt_name"]: {"id": row["id"]} for row in rows}

    @staticmethod
    async def _get_dictionary_by_position(position_id: int) -> int:
        sql = """
        SELECT id_dictionary FROM dictionary_positions dp
        where id = :position_id
        """
        row = await database.fetch_one(sql, {"position_id": position_id})
        return row["id_dictionary"]

    @staticmethod
    async def _batch_insert_data(data: List[Dict]) -> None:
        """Пакетная вставка данных"""
        sql = """
               INSERT INTO dictionary_data
               (id_position, id_attribute, start_date, finish_date, value)
               VALUES (:id_position, :id_attribute, :start_date, :finish_date, :value)
           """
        await database.execute_many(sql, data)

    @staticmethod
    def _dates_overlap(row: dict, parent_row: dict) -> bool:
        return (
            parent_row["start_date"] < row["finish_date"]
            and parent_row["finish_date"] > row["start_date"]
        )

    @staticmethod
    async def _update_position_relations(position_id: int, dictionary_id: int) -> None:
        """
        Метод для пересчета иерархии для позиции
        :param position_id:
        :param dictionary_id:
        :return:
        """
        try:
            # Удаляем старые отношения
            await database.execute(
                "DELETE FROM dictionary_relations WHERE id_positions = :id",
                {"id": position_id},
            )

            # Получаем все родительские коды одним запросом
            parent_codes = await database.fetch_all(
                """SELECT dd.value, dd.start_date, dd.finish_date
                FROM dictionary_data dd
                JOIN dictionary_attribute da ON dd.id_attribute = da.id
                WHERE dd.id_position = :id_position AND da.alt_name = 'PARENT_CODE' """,
                {"id_position": position_id},
            )

            # Подготавливаем данные для пакетной вставки
            relations_to_insert = []

            for code in parent_codes:
                candidates = await database.fetch_all(
                    """SELECT dd.id_position, dd.start_date, dd.finish_date
                    FROM dictionary_data dd
                    JOIN dictionary_attribute da ON dd.id_attribute = da.id
                    WHERE da.id_dictionary = :id_dictionary
                    AND da.alt_name = 'CODE'
                    AND dd.value = CAST(:parent_code AS text)""",
                    {"id_dictionary": dictionary_id, "parent_code": code["value"]},
                )

                for candidate in candidates:
                    if not (
                        code["start_date"] < candidate["finish_date"]
                        and code["finish_date"] > candidate["start_date"]
                    ):
                        continue

                    relations_to_insert.append(
                        {
                            "id_positions": position_id,
                            "id_parent_positions": candidate["id_position"],
                            "start_date": max(
                                code["start_date"], candidate["start_date"]
                            ),
                            "finish_date": min(
                                code["finish_date"], candidate["finish_date"]
                            ),
                        }
                    )
            # Вставляем все отношения одним запросом
            if relations_to_insert:
                await database.execute_many(
                    """INSERT INTO dictionary_relations
                    (id_positions, id_parent_positions, start_date, finish_date)
                    VALUES (:id_positions, :id_parent_positions,
                    :start_date, :finish_date)""",
                    relations_to_insert,
                )

            logger.info("Successfully updated relations for position: %s", position_id)
        except Exception as e:
            logger.error(
                "Failed to update relations for position %d: %s", position_id, str(e)
            )

    @staticmethod
    async def import_data(dictionary_id: int, df: pd.DataFrame) -> None:
        """
        импорт значений справочника из pandas dataframe
        :param dictionary_id: идентификатор справочника
        :param df: импортированный dataframe
        :return:
        """

        if not {"CODE", "NAME"}.issubset(df.columns):
            logger.error("Required columns CODE or NAME are missing")
            raise ValueError("DataFrame must contain CODE and NAME columns")

        # Получаем все необходимые данные одним запросом
        dates = await AttributeManager._fetch_dates(dictionary_id)
        attributes_info = await AttributeManager._get_attributes_info(dictionary_id)

        # Фильтруем DataFrame один раз
        valid_rows = df[df["CODE"].notna() & df["NAME"].notna()]
        total_rows = len(valid_rows)

        # Создаем все позиции одним запросом
        position_ids = await AttributeManager._batch_create_positions(
            dictionary_id, total_rows
        )

        # Подготавливаем данные для пакетной вставки
        data_to_insert = []
        valid_attributes = set(attributes_info.keys()) & set(df.columns)

        for idx, (_, row) in enumerate(valid_rows.iterrows()):
            position_id = position_ids[idx]
            for attr in valid_attributes:
                value = str(row[attr])
                clean_value = (
                    None
                    if value.strip().lower() in AttributeManager.NULL_VALUES
                    else value
                )

                data_to_insert.append(
                    {
                        "id_position": position_id,
                        "id_attribute": attributes_info[attr]["id"],
                        "start_date": dates["start_date"],
                        "finish_date": dates["finish_date"],
                        "value": clean_value,
                    }
                )

                # Вставляем батчами
                if len(data_to_insert) >= AttributeManager.BATCH_SIZE:
                    await AttributeManager._batch_insert_data(data_to_insert)
                    data_to_insert = []

        # Вставляем оставшиеся записи
        if data_to_insert:
            await AttributeManager._batch_insert_data(data_to_insert)

        # Генерируем отношения
        await AttributeManager.generate_relations_for_dictionary(dictionary_id)

    @staticmethod
    async def generate_relations_for_dictionary(dictionary_id: int) -> None:
        """
        Расставляем иерархию для справочника
        :param dictionary_id:  идентификатор справочника
        :return:
        """

        # Получаем все позиции одним запросом
        positions = await database.fetch_all(
            "SELECT id FROM dictionary_positions WHERE id_dictionary = :id_dictionary",
            {"id_dictionary": dictionary_id},
        )

        # Используем asyncio.gather для параллельного выполнения
        tasks = [
            AttributeManager._update_position_relations(position["id"], dictionary_id)
            for position in positions
        ]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _get_required_fields(dictionary_id: int) -> List[str]:
        """
        Получение обязательных полей для справочника
        :param dictionary_id: идентификатор справочника
        :return: справочник полей
        """
        sql = """
                select alt_name from dictionary_attribute
                where id_dictionary =:id_dictionary
                and required=true
        """
        rows = await database.fetch_all(sql, {"id_dictionary": dictionary_id})
        return [row["alt_name"] for row in rows]

    @staticmethod
    async def _delete_nested_period(
        position_id: int,
        attribute_id: int,
        start_date: datetime.date,
        finish_date: datetime.date,
    ) -> None:
        """
         Удаляем значения, полностью попадающие в указанный временной период

        Args:
            position_id: идентификатор позиции
            attribute_id: идентификатор атрибута
            start_date: начало действия
            finish_date: конец действия
        Raises:
        ValueError: Если даты некорректны
        """
        # Валидация дат
        if start_date > finish_date:
            raise ValueError("Start date cannot be after finish date")

        sql = """
               DELETE FROM dictionary_data
               WHERE id_position = :position_id
               AND id_attribute = :attribute_id
               AND start_date >= :start_date
               AND finish_date <= :finish_date
           """

        try:
            await database.execute(
                sql,
                {
                    "position_id": position_id,
                    "attribute_id": attribute_id,
                    "start_date": start_date,
                    "finish_date": finish_date,
                },
            )
            logger.debug(
                "Deleted nested period for position %d, attribute %d (%s to %s)",
                position_id,
                attribute_id,
                start_date,
                finish_date,
            )
        except Exception as e:
            logger.error(
                "Failed to delete nested period for position %d, attribute %d: %s",
                position_id,
                attribute_id,
                str(e),
            )
            raise

    @staticmethod
    async def _shift_next_period(
        position_id: int,
        attribute_id: int,
        finish_date: datetime.date,
        value: str,
    ) -> datetime.date:
        """

        Корректирует следующий временной период для атрибута позиции.

        Логика работы:
        - Если следующий период имеет другое значение - сдвигаем его начало
        - Если значения совпадают - объединяем периоды

        Args:
            position_id: ID позиции справочника
            attribute_id: ID атрибута
            finish_date: Дата окончания текущего периода
            value: Значение текущего периода

        Returns:
            date: Новая дата окончания (либо исходная, либо объединенного периода)

        Raises:
            ValueError: Если данные некорректны
        """

        # Получаем следующий период
        next_period = await database.fetch_one(
            """
            SELECT id, value, finish_date
            FROM dictionary_data
            WHERE id_position = :position_id
              AND id_attribute = :attribute_id
              AND start_date <= :finish_date
              AND finish_date > :finish_date
            """,
            {
                "position_id": position_id,
                "attribute_id": attribute_id,
                "finish_date": finish_date,
            },
        )
        if not next_period:
            return finish_date

            # Обработка разных значений
        if next_period["value"] != value:
            await database.execute(
                """
                UPDATE dictionary_data
                SET start_date = :new_start_date
                WHERE id = :record_id
                """,
                {
                    "new_start_date": finish_date + timedelta(days=1),
                    "record_id": next_period["id"],
                },
            )
            return finish_date

            # Обработка одинаковых значений (объединение периодов)
        await database.execute(
            "DELETE FROM dictionary_data WHERE id = :record_id",
            {"record_id": next_period["id"]},
        )

        return next_period["finish_date"]

    @staticmethod
    async def _shift_previous_period(
        position_id: int,
        attribute_id: int,
        start_date: datetime.date,
        value: str,
    ) -> datetime.date:
        """
             Корректирует предыдущий временной период для атрибута позиции.

        Логика работы:
        - Если предыдущий период имеет такое же значение - объединяет периоды
        - Если значения разные - сдвигает конец предыдущего периода

        Args:
            position_id: ID позиции справочника
            attribute_id: ID атрибута
            start_date: Начальная дата нового периода
            value: Значение нового периода

        Returns:
            date: Новая начальная дата
            (либо исходная, либо начало объединенного периода)

        Raises:
            ValueError: Если данные некорректны
        """
        # Получаем предыдущий период
        previous_period = await database.fetch_one(
            """
            SELECT id, value, start_date, finish_date
            FROM dictionary_data
            WHERE id_position = :position_id
              AND id_attribute = :attribute_id
              AND start_date < :start_date
              AND finish_date >= :start_date
            """,
            {
                "position_id": position_id,
                "attribute_id": attribute_id,
                "start_date": start_date,
            },
        )

        if not previous_period:
            return start_date

        # Обработка одинаковых значений (объединение периодов)
        if previous_period["value"] == value:
            await database.execute(
                "DELETE FROM dictionary_data WHERE id = :record_id",
                {"record_id": previous_period["id"]},
            )
            return previous_period["start_date"]

            # Обработка разных значений (сдвиг конца предыдущего периода)
        await database.execute(
            """
            UPDATE dictionary_data
            SET finish_date = :new_finish_date
            WHERE id = :record_id
            """,
            {
                "new_finish_date": start_date - timedelta(days=1),
                "record_id": previous_period["id"],
            },
        )
        return start_date

    @staticmethod
    async def _insert_position(data: Dict) -> None:
        """Пакетная вставка данных"""
        sql = """
                   INSERT INTO dictionary_data
                   (id_position, id_attribute, start_date, finish_date, value)
                   VALUES (:id_position, :id_attribute, :start_date, :finish_date,
                    :value)
               """
        await database.execute(
            sql,
            {
                "id_position": data["id_position"],
                "id_attribute": data["id_attribute"],
                "start_date": data["start_date"],
                "finish_date": data["finish_date"],
                "value": data["value"],
            },
        )

    @staticmethod
    async def create_position(dictionary_id: int, attrs_list: List[AttrShown]) -> None:
        """
        Создание позиции справочника
        :param attrs_list:
        :param dictionary_id:
        :return:
        """
        logger.debug("Creating positions for dictionary %s", dictionary_id)
        data = {attr.name: attr.value for attr in attrs_list}
        try:
            if not data:
                raise ValueError("Empty data provided")

            # Получаем даты из словаря
            dates = {
                "start_date": datetime.strptime(data["START_DATE"], "%Y-%m-%d").date(),
                "finish_date": datetime.strptime(
                    data["FINISH_DATE"], "%Y-%m-%d"
                ).date(),
            }
            df = pd.DataFrame(data=data, index=[0])
            required_fields = await AttributeManager._get_required_fields(dictionary_id)
            data_to_insert = []
            # Validate required fields
            missing_fields = [
                field for field in required_fields if field not in df.columns
            ]
            if missing_fields:
                miss = ", ".join(missing_fields)
                logger.error("Missing fields: %s", miss)
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            attributes_info = await AttributeManager._get_attributes_info(dictionary_id)
            position_id = await AttributeManager._single_create_positions(dictionary_id)
            df.drop(columns=["START_DATE", "FINISH_DATE"], inplace=True)
            valid_attributes = set(attributes_info.keys()) & set(df.columns)
            for attr in valid_attributes:
                value = str(df[attr][0])
                clean_value = (
                    None
                    if value.strip().lower() in AttributeManager.NULL_VALUES
                    else value
                )
                data_to_insert.append(
                    {
                        "id_position": position_id,
                        "id_attribute": attributes_info[attr]["id"],
                        "start_date": dates["start_date"],
                        "finish_date": dates["finish_date"],
                        "value": clean_value,
                    }
                )
            if data_to_insert:
                await AttributeManager._batch_insert_data(data_to_insert)

                # Генерируем отношения
            await AttributeManager._update_position_relations(
                position_id, dictionary_id
            )
        except ValueError as ve:
            logger.error("Validation error: %s", ve)
            raise
        except Exception as e:
            logger.error(
                "Failed to create positions for dictionary %s: %s", dictionary_id, e
            )
            raise Exception("Position creation failed") from e

    @staticmethod
    async def edit_position(position_id: int, attrs_list: List[AttrShown]) -> None:
        """
        Создание позиции справочника
        :param position_id:
        :param attrs_list:
        :return:
        """
        data = {attr.name: attr.value for attr in attrs_list}
        try:
            if not data:
                raise ValueError("Empty data provided")
            # Получаем даты из словаря
            dates = {
                "start_date": datetime.strptime(data["START_DATE"], "%Y-%m-%d").date(),
                "finish_date": datetime.strptime(
                    data["FINISH_DATE"], "%Y-%m-%d"
                ).date(),
            }
            df = pd.DataFrame(data=data, index=[0])
            # Validate required fields
            dictionary_id = await AttributeManager._get_dictionary_by_position(
                position_id
            )
            attributes_info = await AttributeManager._get_attributes_info(dictionary_id)
            df.drop(columns=["START_DATE", "FINISH_DATE"], inplace=True)
            valid_attributes = set(attributes_info.keys()) & set(df.columns)
            for attr in valid_attributes:
                value = str(df[attr].iloc[0]) if not df[attr].empty else None
                clean_value = (
                    None
                    if value.strip().lower() in AttributeManager.NULL_VALUES
                    else value
                )
                await AttributeManager._delete_nested_period(
                    position_id=position_id,
                    attribute_id=attributes_info[attr]["id"],
                    start_date=dates["start_date"],
                    finish_date=dates["finish_date"],
                )
                finsh_date_attr = await AttributeManager._shift_next_period(
                    position_id=position_id,
                    attribute_id=attributes_info[attr]["id"],
                    finish_date=dates["finish_date"],
                    value=clean_value,
                )
                start_date_attr = await AttributeManager._shift_previous_period(
                    position_id=position_id,
                    attribute_id=attributes_info[attr]["id"],
                    start_date=dates["start_date"],
                    value=clean_value,
                )
                await AttributeManager._insert_position(
                    {
                        "id_position": position_id,
                        "id_attribute": attributes_info[attr]["id"],
                        "start_date": start_date_attr,
                        "finish_date": finsh_date_attr,
                        "value": clean_value,
                    }
                )
            await AttributeManager._update_position_relations(
                position_id, dictionary_id
            )
        except ValueError as ve:
            logger.error("Validation error: %s", ve)
            raise
        except Exception as e:
            logger.error(
                "Failed to create positions for dictionary %d: %s ", dictionary_id, e
            )
            raise Exception("Position creation failed") from e
