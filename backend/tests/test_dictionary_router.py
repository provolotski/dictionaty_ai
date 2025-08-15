"""
Тесты для роутера справочников
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, ANY
from datetime import date

from routers.dictionary import dict_router
from services.dictionary_service import DictionaryService

app = FastAPI()
app.include_router(dict_router)
transport = ASGITransport(app=app)


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.create_dictionary", new_callable=AsyncMock)
async def test_create_new_dictionary(mock_create):
    """Тест создания нового справочника"""
    mock_create.return_value = 1
    
    payload = {
        "name": "Test Dictionary",
        "code": "test_001",
        "description": "test data mock",
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
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/newDictionary", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": " Справочник создан"}
    mock_create.assert_awaited_once()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_all_dictionaries", return_value=[])
async def test_list_dictionaries(mock_list):
    """Тест получения списка справочников"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/list")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    mock_list.assert_awaited_once()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_structure", return_value=[])
async def test_get_dictionary_structure(mock_structure):
    """Тест получения структуры справочника"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/structure/?dictionary=1")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    mock_structure.assert_awaited_once_with(1)


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_values", return_value=[])
async def test_get_dictionary_values(mock_get):
    """Тест получения значений справочника"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/dictionary/?dictionary=1")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    mock_get.assert_awaited()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_position_by_code", return_value={"code": "A1"})
async def test_get_value_by_code(mock_get):
    """Тест получения значения по коду"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/dictionaryValueByCode/?dictionary=1&code=A1")

    assert response.status_code == 200
    assert response.json() == {"code": "A1"}
    mock_get.assert_awaited()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_position_by_id", return_value={"id": 1})
async def test_get_value_by_id(mock_get):
    """Тест получения значения по ID"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/dictionaryValueByID?dictionary=1&position_id=10")

    assert response.status_code == 200
    assert response.json() == {"id": 1}
    mock_get.assert_awaited()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.find_dictionary_by_name", return_value={"id": 1, "name": "Test"})
async def test_find_dictionary_by_name(mock_find):
    """Тест поиска справочника по названию"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/findDictionaryByName?name=Test")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Test"}
    mock_find.assert_awaited_once_with("Test")


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.find_dictionary_value", return_value={"id": 2, "name": "Other"})
async def test_find_dictionary_value(mock_find_value):
    """Тест поиска значения в справочнике"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/findDictionaryValue?dictionary=1&findstr=Search")

    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "Other"}
    mock_find_value.assert_awaited_once_with(1, "Search")


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_structure", return_value=[])
async def test_post_get_dictionary_structure(mock_structure):
    """Тест POST запроса для получения структуры справочника"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/structure/?dictionary=1")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    mock_structure.assert_awaited_once_with(1)


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_values", return_value=[])
async def test_post_get_dictionary_values(mock_get):
    """Тест POST запроса для получения значений справочника"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/dictionary/?dictionary=1")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    mock_get.assert_awaited()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_position_by_code", return_value={"code": "A1"})
async def test_post_value_by_code(mock_get):
    """Тест POST запроса для получения значения по коду"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/dictionaryValueByCode/?dictionary=1&code=A1")

    assert response.status_code == 200
    assert response.json() == {"code": "A1"}
    mock_get.assert_awaited()


@pytest.mark.asyncio
async def test_post_value_by_code_missing_param():
    """Тест POST запроса с отсутствующим параметром кода"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/dictionaryValueByCode/?dictionary=1")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary_position_by_id", return_value={"id": 10})
async def test_post_value_by_id(mock_get):
    """Тест POST запроса для получения значения по ID"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/dictionaryValueByID?dictionary=1&position_id=10")

    assert response.status_code == 200
    assert response.json() == {"id": 10}
    mock_get.assert_awaited()


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.find_dictionary_by_name", return_value={"id": 1, "name": "MockDict"})
async def test_post_find_dictionary_by_name(mock_find):
    """Тест POST запроса для поиска справочника по названию"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/findDictionaryByName?name=MockDict")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "MockDict"}
    mock_find.assert_awaited_once_with("MockDict")


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.find_dictionary_value", return_value={"id": 2, "name": "FoundValue"})
async def test_post_find_dictionary_value(mock_find):
    """Тест POST запроса для поиска значения в справочнике"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/models/findDictionaryValue?dictionary=1&findstr=Search")

    assert response.status_code == 200
    assert response.json() == {"id": 2, "name": "FoundValue"}
    mock_find.assert_awaited_once_with(1, "Search")


@pytest.mark.asyncio
async def test_get_dictionary_value_by_code_missing_code():
    """Тест GET запроса с отсутствующим параметром кода"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/dictionaryValueByCode/?dictionary=1")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_dictionary_value_by_id_missing_position_id():
    """Тест GET запроса с отсутствующим параметром position_id"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/dictionaryValueByID?dictionary=1")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary", return_value={"id": 1, "name": "Test"})
async def test_get_dictionary_by_id(mock_get):
    """Тест получения справочника по ID"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/getDictionaryByID?dictionary_id=1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Test"}
    mock_get.assert_awaited_once_with(1)


@pytest.mark.asyncio
@patch("routers.dictionary.DictionaryService.get_dictionary")
async def test_get_dictionary_by_id_not_found(mock_get):
    """Тест получения несуществующего справочника"""
    from exceptions import DictionaryNotFoundError
    
    mock_get.side_effect = DictionaryNotFoundError(999)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/models/getDictionaryByID?dictionary_id=999")

    assert response.status_code == 404
    assert "error" in response.json()
    mock_get.assert_awaited_once_with(999)
