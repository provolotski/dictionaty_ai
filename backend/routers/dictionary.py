"""
Endpoint для системы справочников
"""

from datetime import date as datetime_date
from typing import Optional, List, Union
from fastapi.responses import JSONResponse
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from database import get_database
from services.dictionary_service import DictionaryService
from schemas import DictionaryOut, DictionaryIn, AttributeIn, AttributeDict, AttrShown
from utils.logger import setup_logger

logger = setup_logger(__name__)

dict_router = APIRouter(prefix="/models", tags=["Dictionary"])


async def get_dictionary_service():
    """
    Dependency для получения сервиса справочников
    """
    database = await get_database()
    return DictionaryService(database)


@dict_router.post("/newDictionary")
async def create_new_dictionary(
    dictionary: DictionaryIn,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Создание нового справочника

    Args:
        dictionary: Данные справочника
        service: Сервис справочников

    Returns:
        JSONResponse: Результат создания
    """
    try:
        logger.debug(f"=== СОЗДАНИЕ СПРАВОЧНИКА ===")
        logger.debug(f"Получены данные: {dictionary}")
        logger.debug(f"Тип данных: {type(dictionary)}")
        logger.debug(f"Поля справочника:")
        logger.debug(f"  - name: {dictionary.name}")
        logger.debug(f"  - code: {dictionary.code}")
        logger.debug(f"  - description: {dictionary.description}")
        logger.debug(f"  - start_date: {dictionary.start_date}")
        logger.debug(f"  - finish_date: {dictionary.finish_date}")
        logger.debug(f"  - id_type: {dictionary.id_type}")
        logger.debug(f"  - name_eng: {dictionary.name_eng}")
        logger.debug(f"  - name_bel: {dictionary.name_bel}")
        logger.debug(f"  - description_eng: {dictionary.description_eng}")
        logger.debug(f"  - description_bel: {dictionary.description_bel}")
        logger.debug(f"  - gko: {dictionary.gko}")
        logger.debug(f"  - organization: {dictionary.organization}")
        logger.debug(f"  - classifier: {dictionary.classifier}")
        
        logger.info(f"Вызов service.create_dictionary с данными: {dictionary}")
        dictionary_id = await service.create_dictionary(dictionary)
        
        logger.info(f"Справочник успешно создан с ID: {dictionary_id}")
        logger.debug(f"Возвращаем ответ: {{'message': 'Справочник создан', 'id': {dictionary_id}}}")
        
        return JSONResponse(
            content={"message": "Справочник создан", "id": dictionary_id},
            status_code=201
        )
    except Exception as e:
        logger.error(f"=== ОШИБКА СОЗДАНИЯ СПРАВОЧНИКА ===")
        logger.error(f"Тип ошибки: {type(e)}")
        logger.error(f"Сообщение об ошибке: {str(e)}")
        logger.error(f"Детали ошибки:", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.get("/getMetaDictionary")
async def get_meta_dictionary_by_id(
    dictionary_id: int,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение метаинформации справочника

    Args:
        dictionary_id: ID справочника
        service: Сервис справочников

    Returns:
        DictionaryOut: Метаинформация справочника
    """
    try:
        return await service.get_dictionary(dictionary_id)
    except Exception as e:
        logger.error(f"Ошибка получения метаинформации справочника {dictionary_id}: {e}")
        raise HTTPException(status_code=404, detail="Справочник не найден")


@dict_router.post("/EditDictionary", response_model=DictionaryIn)
async def edit_dictionary(
    dictionary_id: int,
    dictionary: DictionaryIn,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Редактирование справочника

    Args:
        dictionary_id: ID справочника
        dictionary: Новые данные
        service: Сервис справочников

    Returns:
        DictionaryIn: Обновленные данные
    """
    try:
        success = await service.update_dictionary(dictionary_id, dictionary)
        if success:
            return dictionary
        else:
            raise HTTPException(status_code=404, detail="Справочник не найден")
    except Exception as e:
        logger.error(f"Ошибка редактирования справочника {dictionary_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.post("/CreatePosition")
async def create_position(
    dictionary_id: int,
    attrs: List[AttrShown],
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Создание позиции в справочнике

    Args:
        dictionary_id: ID справочника
        attrs: Атрибуты позиции
        service: Сервис справочников

    Returns:
        JSONResponse: Результат создания
    """
    try:
        # Здесь должна быть логика создания позиции
        logger.info(f"Создание позиции в справочнике {dictionary_id}")
        return JSONResponse(
            content={"message": "Позиция создана"},
            status_code=201
        )
    except Exception as e:
        logger.error(f"Ошибка создания позиции в справочнике {dictionary_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.post("/EditPosition")
async def edit_position(
    position_id: int,
    attrs: List[AttrShown],
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Редактирование позиции в справочнике

    Args:
        position_id: ID позиции
        attrs: Новые атрибуты
        service: Сервис справочников

    Returns:
        JSONResponse: Результат редактирования
    """
    try:
        # Здесь должна быть логика редактирования позиции
        logger.info(f"Редактирование позиции {position_id}")
        return JSONResponse(
            content={"message": "Позиция обновлена"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования позиции {position_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.get(path="/list", response_model=List[DictionaryOut])
async def list_dictionaries(
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение списка всех справочников

    Args:
        service: Сервис справочников

    Returns:
        List[DictionaryOut]: Список справочников
    """
    try:
        return await service.get_all_dictionaries()
    except Exception as e:
        logger.error(f"Ошибка получения списка справочников: {e}")
        return []


@dict_router.get(path="/getDictionaryByID", response_model=None)
async def get_dictionary_by_id(
    dictionary_id: int,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Union[DictionaryOut, JSONResponse]:
    """
    Получение справочника по ID

    Args:
        dictionary_id: ID справочника
        service: Сервис справочников

    Returns:
        Union[DictionaryOut, JSONResponse]: Данные справочника или ошибка
    """
    try:
        return await service.get_dictionary(dictionary_id)
    except Exception as e:
        logger.error(f"Ошибка получения справочника {dictionary_id}: {e}")
        return JSONResponse(
            content={"error": "Справочник не найден"},
            status_code=404
        )


@dict_router.get(path="/deleteDictonaryById", response_model=DictionaryOut)
@dict_router.post(path="/deleteDictonaryById", response_model=DictionaryOut)
async def delete_dictionary_by_id(
    dictionary_id: int,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Удаление справочника по ID

    Args:
        dictionary_id: ID справочника
        service: Сервис справочников

    Returns:
        DictionaryOut: Удаленный справочник
    """
    try:
        # Получаем справочник перед удалением
        dictionary = await service.get_dictionary(dictionary_id)
        success = await service.delete_dictionary(dictionary_id)
        
        if success:
            return dictionary
        else:
            raise HTTPException(status_code=404, detail="Справочник не найден")
    except Exception as e:
        logger.error(f"Ошибка удаления справочника {dictionary_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.get(path="/structure/", response_model=List[AttributeIn])
@dict_router.post(path="/structure/", response_model=List[AttributeIn])
async def get_dictionary_structure(
    dictionary: int,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение структуры справочника

    Args:
        dictionary: ID справочника
        service: Сервис справочников

    Returns:
        List[AttributeIn]: Структура справочника
    """
    try:
        # Здесь должна быть логика получения структуры
        logger.info(f"Получение структуры справочника {dictionary}")
        return []
    except Exception as e:
        logger.error(f"Ошибка получения структуры справочника {dictionary}: {e}")
        return []


@dict_router.post(path="/add_attribute/", response_model=AttributeDict)
async def add_attribute(
    attribute: AttributeDict,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Добавление атрибута к справочнику

    Args:
        attribute: Данные атрибута
        service: Сервис справочников

    Returns:
        AttributeDict: Добавленный атрибут
    """
    try:
        # Здесь должна быть логика добавления атрибута
        logger.info(f"Добавление атрибута к справочнику {attribute.id_dictionary}")
        return attribute
    except Exception as e:
        logger.error(f"Ошибка добавления атрибута: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.get(path="/dictionaryValueByCode/")
@dict_router.post(path="/dictionaryValueByCode/")
async def get_dictionary_value_by_code(
    dictionary: int,
    code: str,
    date: Optional[datetime_date] = None,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение значения справочника по коду

    Args:
        dictionary: ID справочника
        code: Код позиции
        date: Дата (опционально)
        service: Сервис справочников

    Returns:
        Dict: Значение позиции
    """
    try:
        if date is None:
            date = datetime_date.today()
        
        # Здесь должна быть логика получения значения по коду
        logger.info(f"Получение значения по коду {code} в справочнике {dictionary}")
        return {"code": code, "dictionary": dictionary, "date": date}
    except Exception as e:
        logger.error(f"Ошибка получения значения по коду {code}: {e}")
        raise HTTPException(status_code=404, detail="Значение не найдено")


@dict_router.get(path="/dictionaryValueByID")
@dict_router.post(path="/dictionaryValueByID")
async def get_dictionary_value_by_id(
    dictionary: int,
    position_id: int,
    date: Optional[datetime_date] = None,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение значения справочника по ID позиции

    Args:
        dictionary: ID справочника
        position_id: ID позиции
        date: Дата (опционально)
        service: Сервис справочников

    Returns:
        Dict: Значение позиции
    """
    try:
        if date is None:
            date = datetime_date.today()
        
        # Здесь должна быть логика получения значения по ID
        logger.info(f"Получение значения по ID {position_id} в справочнике {dictionary}")
        return {"id": position_id, "dictionary": dictionary, "date": date}
    except Exception as e:
        logger.error(f"Ошибка получения значения по ID {position_id}: {e}")
        raise HTTPException(status_code=404, detail="Значение не найдено")


@dict_router.get(path="/findDictionaryByName")
@dict_router.post(path="/findDictionaryByName")
async def find_dictionary_by_name(
    name: str,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Поиск справочников по названию

    Args:
        name: Название для поиска
        service: Сервис справочников

    Returns:
        List[DictionaryOut]: Найденные справочники
    """
    try:
        return await service.find_dictionary_by_name(name)
    except Exception as e:
        logger.error(f"Ошибка поиска справочников по названию '{name}': {e}")
        return []


@dict_router.get(path="/findDictionaryValue")
@dict_router.post(path="/findDictionaryValue")
async def find_dictionary_value(
    dictionary: int,
    findstr: str,
    date: Optional[datetime_date] = None,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Поиск значений в справочнике

    Args:
        dictionary: ID справочника
        findstr: Строка для поиска
        date: Дата (опционально)
        service: Сервис справочников

    Returns:
        List: Найденные значения
    """
    try:
        if date is None:
            date = datetime_date.today()
        
        # Здесь должна быть логика поиска значений
        logger.info(f"Поиск значений '{findstr}' в справочнике {dictionary}")
        return []
    except Exception as e:
        logger.error(f"Ошибка поиска значений '{findstr}': {e}")
        return []


@dict_router.post(path="/importCSV")
async def import_csv(
    dictionary: int,
    file: UploadFile = File(...),
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Импорт данных из CSV файла

    Args:
        dictionary: ID справочника
        file: CSV файл
        service: Сервис справочников

    Returns:
        JSONResponse: Результат импорта
    """
    try:
        # Читаем содержимое файла
        content = await file.read()
        
        # Импортируем данные
        result = await service.import_csv_data(dictionary, content, file.filename)
        
        return JSONResponse(
            content=result,
            status_code=200
        )
    except Exception as e:
        logger.error(f"Ошибка импорта CSV в справочник {dictionary}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@dict_router.get(path="/dictionary/")
@dict_router.post(path="/dictionary/")
async def get_dictionary(
    dictionary: int,
    date: Optional[datetime_date] = None,
    service: DictionaryService = Depends(get_dictionary_service)
):
    """
    Получение всех значений справочника

    Args:
        dictionary: ID справочника
        date: Дата (опционально)
        service: Сервис справочников

    Returns:
        List: Значения справочника
    """
    try:
        return await service.get_dictionary_values(dictionary, date)
    except Exception as e:
        logger.error(f"Ошибка получения значений справочника {dictionary}: {e}")
        return []
