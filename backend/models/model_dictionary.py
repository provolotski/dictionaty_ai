"""
Модуль обработки справочников
"""

# pylint: disable=import-error
import datetime
import logging

from typing import List

import schemas
from database import database
from config import settings
from models.model_attribute import AttributeManager
from schemas import DictionaryPosition
import json

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT,
    handlers=[logging.FileHandler(settings.LOG_FILE), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class DictionaryService:
    """
    Класс по управлению справочниками
    """

    # Константы
    DEFAULT_CAPACITY = 250

    REQUIRED_ATTRIBUTES = [
        {
            "name": "Наименование",
            "alt_name": "NAME",
            "required": True,
            "id_attribute_type": 0,
        },
        {"name": "Код", "alt_name": "CODE", "required": True, "id_attribute_type": 0},
        {
            "name": "Код родительской позиции",
            "alt_name": "PARENT_CODE",
            "required": True,
            "id_attribute_type": 0,
        },
        {
            "name": "Признак полноты итога",
            "alt_name": "FULL_SUM",
            "required": True,
            "id_attribute_type": 3,
        },
        {
            "name": "Дата начала действия позиции",
            "alt_name": "START_DATE",
            "required": True,
            "id_attribute_type": 2,
        },
        {
            "name": "Дата окончания действия позиции",
            "alt_name": "FINISH_DATE",
            "required": True,
            "id_attribute_type": 2,
        },
        {
            "name": "Наименование на белорусском языке",
            "alt_name": "NAME_BEL",
            "required": True,
            "id_attribute_type": 0,
        },
        {
            "name": "Наименование на английском языке",
            "alt_name": "NAME_ENG",
            "required": True,
            "id_attribute_type": 0,
        },
        {
            "name": "Описание",
            "alt_name": "Descr",
            "required": False,
            "id_attribute_type": 0,
        },
        {
            "name": "Описание на белорусском языке",
            "alt_name": "Descr_BEL",
            "required": False,
            "id_attribute_type": 0,
        },
        {
            "name": "Описание на английском языке",
            "alt_name": "Descr_ENG",
            "required": False,
            "id_attribute_type": 0,
        },
        {
            "name": "Коментарий",
            "alt_name": "COMMENT",
            "required": False,
            "id_attribute_type": 0,
        },
    ]

    @staticmethod
    async def get_all() -> List[schemas.DictionaryOut]:
        """Получение всех справочников"""

        sql = """
        select id, name, code, description,start_date,
        finish_date, name_eng, name_bel, description_eng,
        description_bel, gko, organization,classifier,id_status, id_type,
        created_at, updated_at
        from dictionary
        """
        rows = await database.fetch_all(sql)
        return [schemas.DictionaryOut(**dict(row)) for row in rows]

    @staticmethod
    async def get_dictionary_by_id(dictionary_id: int) -> schemas.DictionaryOut:
        """Получение справочника по ID """

        sql = """
        select id, name, code, description,start_date,
        finish_date, name_eng, name_bel, description_eng,
        description_bel, gko, organization,classifier,id_status, id_type,
        created_at, updated_at
        from dictionary
        where id =:dictionary_id
        """
        row = await database.fetch_one(sql, {"dictionary_id": dictionary_id})
        return schemas.DictionaryOut(**dict(row))

    @staticmethod
    async def delete_dictionary_by_id(dictionary_id: int) -> bool:
        """Получение всех справочников"""
        try:
            sql = "delete from dictionary_attribute where id_dictionary =:dictionary_id"
            await database.execute(sql, {"dictionary_id": dictionary_id})
            sql = "delete from dictionary where id =:dictionary_id"
            await database.execute(sql, {"dictionary_id": dictionary_id})
            return True
        except Exception:
            return False

    @staticmethod
    async def find_dictionary_by_name(name: str) -> List[schemas.DictionaryOut]:
        """
        Поиск справочника по имени
        :param name:
        :return:
        """
        logger.debug("поиск справочника по имени поисковая строка:%s", name)
        sql = """
            select id, name, code, description,start_date, finish_date,
            name_eng, name_bel, description_eng,
            description_bel, gko, organization,classifier,id_status, id_type,
            created_at, updated_at
            from dictionary where name like
            '%'||:name||'%'
            """
        rows = await database.fetch_all(sql, {"name": name})
        return [schemas.DictionaryOut(**dict(row)) for row in rows]

    @staticmethod
    async def create(dictionary) -> int:
        """
        Создание справочника
        :param dictionary: DictionaryIn объект или словарь с данными
        :return:
        """
        logger.debug(f"=== СОЗДАНИЕ СПРАВОЧНИКА В МОДЕЛИ ===")
        logger.debug(f"Входные данные: {dictionary}")
        logger.debug(f"Тип данных: {type(dictionary)}")
        
        # Преобразуем в словарь если это Pydantic модель
        if hasattr(dictionary, 'model_dump'):
            dictionary_data = dictionary.model_dump()
            logger.debug(f"Модель данных: {dictionary_data}")
        else:
            dictionary_data = dictionary
            logger.debug(f"Данные уже в виде словаря: {dictionary_data}")

        sql = """
            insert into dictionary (name, code, description,start_date,
            finish_date, change_date, name_eng,
            name_bel,description_eng, description_bel, gko,
            organization,classifier,id_status, id_type, created_at, updated_at) values (
            :name, :code, :description, :start_date,
            :finish_date, current_date, :name_eng, :name_bel,
            :description_eng, :description_bel, :gko,
            :organization, :classifier,:id_status,:id_type, current_timestamp, current_timestamp) returning id
        """

        logger.debug(f"SQL запрос: {sql}")
        logger.debug(f"Значения для SQL: {dictionary_data}")

        try:
            dict_id = await database.execute(sql, values=dictionary_data)
            logger.debug(f"Справочник создан в БД с ID: {dict_id}")

            # Создаем обязательные параметры
            logger.debug(f"Создание обязательных атрибутов для справочника {dict_id}...")
            logger.debug(f"Обязательные атрибуты: {DictionaryService.REQUIRED_ATTRIBUTES}")

            for attr_config in DictionaryService.REQUIRED_ATTRIBUTES:
                logger.debug(f"Создание атрибута: {attr_config}")
                
                # Создаем правильную структуру данных для атрибута
                attr_data = {
                    'id_dictionary': dict_id,
                    'start_date': dictionary_data['start_date'],
                    'finish_date': dictionary_data['finish_date'],
                    'capacity': DictionaryService.DEFAULT_CAPACITY,
                    'name': attr_config['name'],
                    'alt_name': attr_config['alt_name'],
                    'required': attr_config['required'],
                    'id_attribute_type': attr_config['id_attribute_type']
                }
                
                logger.debug(f"Данные атрибута для создания: {attr_data}")
                attr_id = await DictionaryService._create_attribute(attr_data)
                logger.debug(f"Атрибут создан с ID: {attr_id}")

            logger.info("Справочник успешно создан в БД с ID: %d", dict_id)
            return dict_id

        except Exception as e:
            logger.error(f"=== ОШИБКА СОЗДАНИЯ СПРАВОЧНИКА В БД ===")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Сообщение об ошибке: {str(e)}")
            logger.error(f"SQL запрос: {sql}")
            logger.error(f"Значения: {dictionary_data}")
            logger.error(f"Полный traceback:", exc_info=True)
            raise

    @staticmethod
    async def update(dict_id: int, dictionary: schemas.DictionaryIn) -> bool:
        """
        Обновление справочника
        :param dict_id: ID справочника
        :param dictionary: Данные для обновления
        :return: True, если обновление прошло успешно
        """
        sql = """
            update dictionary set
            name = :name,
            code = :code,
            description = :description,
            start_date = :start_date,
            finish_date = :finish_date,
            change_date = current_date,
            name_eng = :name_eng,
            name_bel = :name_bel,
            description_eng = :description_eng,
            description_bel = :description_bel,
            gko = :gko,
            organization = :organization,
            classifier = :classifier,
            id_status = :id_status,
            id_type = :id_type
            where id = :dict_id
        """

        values = dictionary.model_dump()
        values["dict_id"] = dict_id

        await database.execute(sql, values=values)

        # Обновляем обязательные атрибуты (если требуется)

        logger.info("Updated dictionary ID: %d", dict_id)
        return True

    @staticmethod
    async def _create_attribute(attribute_data: dict) -> int:
        """
        Создание атрибута
        :param attribute_data: Словарь с данными атрибута
        :return:
        """
        logger.debug(f"=== СОЗДАНИЕ АТРИБУТА ===")
        logger.debug(f"Входные данные атрибута: {attribute_data}")
        logger.debug(f"Тип данных: {type(attribute_data)}")

        sql = """
            INSERT INTO dictionary_attribute (
                id_dictionary, name, required, start_date,
                finish_date, alt_name, id_attribute_type, capacity
            ) VALUES (
                :id_dictionary, :name, :required, :start_date,
                :finish_date, :alt_name, :id_attribute_type, :capacity
            ) RETURNING id
        """

        logger.debug(f"SQL запрос для атрибута: {sql}")
        logger.debug(f"Значения для SQL атрибута: {attribute_data}")

        try:
            attr_id = await database.execute(sql, values=attribute_data)
            logger.debug(f"Атрибут успешно создан в БД с ID: {attr_id}")
            return attr_id
        except Exception as e:
            logger.error(f"=== ОШИБКА СОЗДАНИЯ АТРИБУТА В БД ===")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Сообщение об ошибке: {str(e)}")
            logger.error(f"SQL запрос: {sql}")
            logger.error(f"Значения: {attribute_data}")
            logger.error(f"Полный traceback:", exc_info=True)
            raise

    @staticmethod
    async def insert_dictionary_values(id_dictionary: int, dataframe) -> True | False:
        try:
            await AttributeManager.import_data(id_dictionary, dataframe)
            return True
        except Exception as e:
            logger.error(e)
            return False

    @staticmethod
    async def get_dictionary_values(
        dictionary_id: int, date: datetime.date
    ) -> list[schemas.DictionaryPosition]:
        """
        Получение справочника целиком
        :param dictionary_id:
        :param date:
        :return:
        """
        logger.info(
            f"получение всех значений справочника с id ={dictionary_id}  на дату {date}"
        )

        sql = """
        WITH position_data AS (
 select
    dp.id,
    t1.id_parent_positions AS parent_id,
    t1.value AS parent_code,
    dp.id_dictionary
            FROM dictionary_positions dp
            left join
            ( select dr.id_positions, dr.id_parent_positions,dd1.value
            from  dictionary_relations dr
            JOIN dictionary_data dd1 ON dd1.id_position = dr.id_positions
            JOIN dictionary_attribute da1
            ON dd1.id_attribute = da1.id AND da1.alt_name = 'PARENT_CODE'
            where  :dt between dr.start_date and dr.finish_date
            and  :dt  between dd1.start_date and dd1.finish_date
            ) t1 on (dp.id = t1.id_positions)
            WHERE dp.id_dictionary = :id_dictionary
   ),
        attributes AS (
   select  pd.id,
                pd.parent_id,
                pd.parent_code,
                da.name AS attr_name,
                dd.value AS attr_value from position_data pd
   join dictionary_attribute da  on pd.id_dictionary =da.id_dictionary
   left outer join dictionary_data dd
   on (dd.id_position =pd.id and dd.id_attribute =da.id )
   where  :dt between dd.start_date and dd.finish_date
         )
        SELECT
            id,
            parent_id,
            parent_code,
            json_agg(
                json_build_object('name', attr_name, 'value', attr_value)
            ) AS attrs
        FROM attributes
        GROUP BY id, parent_id, parent_code
        ORDER BY id
        """
        rows = await database.fetch_all(
            sql, {"id_dictionary": dictionary_id, "dt": date}
        )
        logger.debug("количество строк %d", len(rows))
        # Преобразуем данные в формат DictionaryPosition
        positions = []
        for row in rows:
            row_dict = dict(row)
            logger.debug(f"row_dict: {row_dict}")
            # Извлекаем данные из атрибутов
            if isinstance(row_dict['attrs'], str):
                attrs = json.loads(row_dict['attrs'])
            else:
                attrs = row_dict['attrs']
            logger.debug(f"attrs: {attrs}")
            code = None
            name = None
            description = None
            
            for attr in attrs:
                attr_name = attr.get('name', '').lower()
                attr_value = attr.get('value')
                
                if attr_name == 'код':
                    code = attr_value
                elif attr_name == 'наименование':
                    name = attr_value
                elif attr_name == 'описание':
                    description = attr_value
            
            # Создаем объект DictionaryPosition с fallback значениями
            position = schemas.DictionaryPosition(
                id=row_dict['id'],
                code=code or f"POS_{row_dict['id']}",  # Fallback если код не найден
                name=name or f"Позиция {row_dict['id']}",  # Fallback если название не найдено
                description=description,
                start_date=date,  # Используем переданную дату как start_date
                finish_date=date,  # Используем переданную дату как finish_date
                parent_id=row_dict['parent_id'],
                dictionary_id=dictionary_id  # Используем переданный dictionary_id
            )
            positions.append(position)
        
        return positions

    @staticmethod
    async def get_dictionary_structure(dictionary_id: int) -> list[schemas.AttributeIn]:
        logger.debug(f"получаем структуру справочника с id = {dictionary_id}")
        sql = (
            "select id, name, id_attribute_type,"
            "start_date,finish_date,required,capacity, alt_name  from "
            "dictionary_attribute where id_dictionary =:id"
        )
        rows = await database.fetch_all(sql, values={"id": dictionary_id})
        return [schemas.AttributeIn(**dict(row)) for row in rows]

    @staticmethod
    async def create_attr_in_dictionary(attribute: schemas.AttributeDict):
        logger.debug("create new attribute")
        await DictionaryService._create_attribute(attribute)

    @staticmethod
    async def can_delete_dictionary(dictionary_id: int) -> bool:
        sql = """select count(*) from dictionary_positions dp
        where dp.id_dictionary = :id_dictionary"""

        rows = await database.fetch_one(sql, {"id_dictionary": dictionary_id})
        return int(rows[0]) == 0

    @staticmethod
    async def get_dictionary_position_by_code(
        dictionary_id: int, code: str, date: datetime.date
    ) -> list[schemas.DictionaryPosition]:
        """
        Получение позиции справочника по коду
        :param dictionary_id:
        :param code:
        :param date:
        :return:
        """

        logger.debug(
            "получение позиции справочника с id = %d по коду %s  на дату %s",
            dictionary_id,
            code,
            str(date),
        )
        sql = """
                WITH position_data AS (
         select
            dp.id,
            t1.id_parent_positions AS parent_id,
            t1.value AS parent_code,
            dp.id_dictionary
                    FROM dictionary_positions dp
                    left join
                    ( select dr.id_positions, dr.id_parent_positions,dd1.value
                    from  dictionary_relations dr
                    JOIN dictionary_data dd1 ON dd1.id_position = dr.id_positions
                    JOIN dictionary_attribute da1
                    ON dd1.id_attribute = da1.id AND da1.alt_name = 'PARENT_CODE'
                    where  :dt between dr.start_date and dr.finish_date
                    and  :dt  between dd1.start_date and dd1.finish_date
                    ) t1 on (dp.id = t1.id_positions)
                    WHERE dp.id_dictionary = :id_dictionary
                    and exists (
                    select null
                    from dictionary_data dd, dictionary_attribute da
           where dd.id_attribute =da.id
           and da.alt_name ='CODE'
           and dd.value  like '%'||:code||'%'
           and dd.id_position =dp.id
           and :dt between dd.start_date and dd.finish_date)
           ),
                attributes AS (
           select  pd.id,
                        pd.parent_id,
                        pd.parent_code,
                        da.name AS attr_name,
                        dd.value AS attr_value from position_data pd
           join dictionary_attribute da  on pd.id_dictionary =da.id_dictionary
           left outer join dictionary_data dd on
           (dd.id_position =pd.id and dd.id_attribute =da.id )
           where  :dt between dd.start_date and dd.finish_date
                 )
                SELECT
                    id,
                    parent_id,
                    parent_code,
                    json_agg(
                        json_build_object('name', attr_name, 'value', attr_value)
                    ) AS attrs
                FROM attributes
                GROUP BY id, parent_id, parent_code
                ORDER BY id
                """
        rows = await database.fetch_all(
            sql, {"id_dictionary": dictionary_id, "code": code, "dt": date}
        )
        return [schemas.DictionaryPosition(**dict(row)) for row in rows]

    @staticmethod
    async def get_dictionary_position_by_id(
        dictionary_id: int, id_position: int, date: datetime.date
    ) -> list[DictionaryPosition]:
        """
        Получение позиции справочника по id
        :param dictionary_id: идентификатор справочника
        :param id_position: идентификатор позиции
        :param date:
        :return:
        """
        logger.debug(
            "Получение позиции справочника по ID = %d из справочника %d на дату %s",
            id_position,
            dictionary_id,
            str(date),
        )
        sql = """
                       WITH position_data AS (
                select
                    dp.id,
                   t1.id_parent_positions AS parent_id,
                   t1.value AS parent_code,
                   dp.id_dictionary
                           FROM dictionary_positions dp
                           left join
                           ( select dr.id_positions, dr.id_parent_positions,dd1.value
                           from  dictionary_relations dr
                           JOIN dictionary_data dd1 ON dd1.id_position = dr.id_positions
                           JOIN dictionary_attribute da1 ON
                           dd1.id_attribute = da1.id AND da1.alt_name = 'PARENT_CODE'
                           where :dt between dr.start_date
                           and dr.finish_date
                           and :dt between dd1.start_date and dd1.finish_date
                           ) t1 on (dp.id = t1.id_positions)
                           WHERE dp.id_dictionary = :id_dictionary
                        and dp.id = :id

                  ),
                       attributes AS (
                  select  pd.id,
                               pd.parent_id,
                               pd.parent_code,
                               da.name AS attr_name,
                               dd.value AS attr_value from position_data pd
                  join dictionary_attribute da  on pd.id_dictionary =da.id_dictionary
                  left outer join dictionary_data dd on
                    (dd.id_position =pd.id and dd.id_attribute =da.id )
                   where  :dt between dd.start_date and dd.finish_date
                        )
                       SELECT
                           id,
                           parent_id,
                           parent_code,
                           json_agg(
                               json_build_object('name', attr_name, 'value', attr_value)
                           ) AS attrs
                       FROM attributes
                       GROUP BY id, parent_id, parent_code
                       ORDER BY id;
                       """
        rows = await database.fetch_all(
            sql,
            {"id_dictionary": dictionary_id, "id": id_position, "dt": date},
        )
        return [schemas.DictionaryPosition(**dict(row)) for row in rows]

    @staticmethod
    async def find_dictionary_position_by_expression(
        dictionary_id: int, find_str: str, date: datetime.date
    ) -> List[schemas.DictionaryPosition]:
        logger.debug(
            "поиск значений справочника по  поисковая строка:%s в справочнике %d",
            find_str,
            dictionary_id,
        )
        if date is None:
            date = datetime.date.today()
        sql = """
                       WITH position_data AS (
                select
                    dp.id,
                   t1.id_parent_positions AS parent_id,
                   t1.value AS parent_code,
                   dp.id_dictionary
                           FROM dictionary_positions dp
                           left join
                           ( select dr.id_positions, dr.id_parent_positions,dd1.value
                           from  dictionary_relations dr
                           JOIN dictionary_data dd1 ON dd1.id_position = dr.id_positions
                           JOIN dictionary_attribute da1 ON
                            dd1.id_attribute = da1.id AND da1.alt_name = 'PARENT_CODE'
                           where :dt between dr.start_date
                           and dr.finish_date
                           and :dt between dd1.start_date and dd1.finish_date
                           ) t1 on (dp.id = t1.id_positions)
                           WHERE dp.id_dictionary = :id_dictionary
                           and exists (select null from dictionary_data dd
                            where dd.value  like '%'||:code||'%'
                            and dd.id_position =dp.id
                            and :dt between dd.start_date and dd.finish_date)
                  ),
                       attributes AS (
                  select  pd.id,
                               pd.parent_id,
                               pd.parent_code,
                               da.name AS attr_name,
                               dd.value AS attr_value from position_data pd
                  join dictionary_attribute da  on pd.id_dictionary =da.id_dictionary
                  left outer join dictionary_data dd
                    on (dd.id_position =pd.id and dd.id_attribute =da.id )
                   where  :dt between dd.start_date and dd.finish_date
                        )
                       SELECT
                           id,
                           parent_id,
                           parent_code,
                           json_agg(
                               json_build_object('name', attr_name, 'value', attr_value)
                           ) AS attrs
                       FROM attributes
                       GROUP BY id, parent_id, parent_code
                       ORDER BY id;
                       """
        rows = await database.fetch_all(
            sql, {"id_dictionary": dictionary_id, "code": find_str, "dt": date}
        )
        return [schemas.DictionaryPosition(**dict(row)) for row in rows]
