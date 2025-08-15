import logging
from fastapi import APIRouter, Security, Query
from config import settings
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader


logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    datefmt=settings.log_date,
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

dict_router = APIRouter(prefix="/dict", tags=["dict"])


@dict_router.get("/getList")
async def dict_list(
    authorization_header: str = Security(
        APIKeyHeader(name="Authorization", auto_error=False)
    ),
):
    """
    Получение перечня всех получаемых справочников
    :param authorization_header: access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage = 200, "ok"
    logger.debug(status_code)
    if status_code == 200:
        # logger.info(f'Пользователь {username} запросил перечень справочников')
        # result = await get_dicionaries_list()
        # return result
        return []
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/getStructure")
async def dict_structure(
    id_dict: int = Query(None, description="идентификатор справочника"),
    authorization_header: str = Security(
        APIKeyHeader(name="Authorization", auto_error=False)
    ),
):
    """
    Получение структуры конкретного справочника
    :param id_dict: идентификатор справочника
    :param authorization_header: access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage = 200, "ok"
    # logger.debug(status_code)
    # if status_code == 200:
    #     logger.info(
    #         f"Пользователь {username} запросил структуру справочника с id = {id_dict}"
    #     )
    #     return await get_dictionary_structure(id_dict)
    # else:
    return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/getDictionary")
async def dict_get(
    id_dict: int = Query(None, description="идентификатор справочника"),
    # authorization_header: str = Security(
    #     APIKeyHeader(name="Authorization", auto_error=False)
    # ),
):
    """
    Получение значений справочников по идентификатору
    :param id_dict: идентификатор справочника
    :param authorization_header: access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage, username = 401, "Не авторизованный пользователь", None
    logger.debug(status_code)
    if status_code == 200:
        logger.info(f"Пользователь {username} запросил справочник с id = {id_dict}")
    # result = await get_dictionary_values(id_dict)
    # return result
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/getDictionaryValueByCode")
async def dict_get(
    # authorization_header: str = Security(
    #     APIKeyHeader(name="Authorization", auto_error=False)
    # ),
    id_dict: int = Query(None, description="идентификатор справочника"),
    code: str = Query(None, description="код значения"),
):
    """
    Получение значений справочника по коду
    :param id_dict: идентификатор справочника
    :param code: код значения
    :param authorization_header: access token аутентификации, передается в заголовке
    :return:  json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage, username = 401, "Не авторизованный пользователь", None
    logger.debug(status_code)
    if status_code == 200:
        logger.info(
            f"Пользователь {username} запросил из справочниа с id = {id_dict} значение по коду {code}"
        )
        # result = await get_dictionary_value_by_code(id_dict, code)
        # return result
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/getDictionaryValueByID")
async def dict_get(
    id_dict: int = Query(None, description="идентификатор справочника"),
    id: int = Query(None, description="идентификатор значения"),
    # authorization_header: str = Security(
    #     APIKeyHeader(name="Authorization", auto_error=False)
    # ),
):
    """
    Получение значений справочника по ID
    :param id_dict: идентификатор справочника
    :param id: ижентификатор значения
    :param authorization_header: access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage, username = 401, "Не авторизованный пользователь", None
    logger.debug(status_code)
    if status_code == 200:
        logger.info(
            f"Пользователь {username} запросил из справочниа с id = {id_dict} значение по ID {id}"
        )
        # result = await get_dictionary_value_by_id(id_dict, id)
        # return result
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/findDictionaryValueByName")
async def dict_get(
    id_dict: int = Query(None, description="идентификатор справочника"),
    name: str = Query(None, description="строка поиска"),
    # authorization_header: str = Security(
    #     APIKeyHeader(name="Authorization", auto_error=False)
    # ),
):
    """
    Поиск значения справочника по наименованию позиуии
    :param id_dict: идентификатор справочника
    :param name: строка поиска
    :param authorization_header: access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage, username = 401, "Не авторизованный пользователь", None
    logger.debug(status_code)
    if status_code == 200:
        logger.info(
            f"Пользователь {username} запросил поиск из справочниа с id = {id_dict} значение с наименованием {name}"
        )
        # result = await get_dictionary_value_by_name(id_dict, name)
        # return result
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)


@dict_router.get("/findDictionaryByName")
async def dict_get(
    name: str = Query(None, description="строка поиска"),
    # authorization_header: str = Security(
    #     APIKeyHeader(name="Authorization", auto_error=False)
    # ),
):
    """
    Поиск справочника по наименованию
    :param name: строка поиска
    :param authorization_header:  access token аутентификации, передается в заголовке
    :return: json list
    """
    # status_code, errmessage, username = await check_token(authorization_header)
    status_code, errmessage, username = 401, "Не авторизованный пользователь", None
    logger.debug(status_code)
    if status_code == 200:
        logger.info(f"Пользователь {username} запросил поиск справочниа по имени{name}")
        # result = await get_dictionary_by_name(name)
        # return result
    else:
        return JSONResponse(content={"message": errmessage}, status_code=status_code)
