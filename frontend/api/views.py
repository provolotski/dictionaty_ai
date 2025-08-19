"""
Views для проксирования API запросов к backend
"""
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
import logging
from datetime import date

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy_api_request(request, path):
    """
    Проксирует API запросы к backend
    """
    logger.info(f"=== ПРОКСИРОВАНИЕ API ЗАПРОСА ===")
    logger.info(f"Метод запроса: {request.method}")
    logger.info(f"Путь запроса: {path}")
    logger.info(f"Полный URL: {request.path}")
    logger.info(f"Заголовки запроса:")
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            logger.info(f"  {key}: {value}")
    
    try:
        # Формируем полный URL для backend
        backend_url = f"{settings.API_DICT['BASE_URL']}/{path}"
        logger.info(f"URL backend: {backend_url}")
        
        # Получаем заголовки запроса
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                # Преобразуем HTTP_HEADER_NAME в Header-Name
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        
        # Убираем Django-специфичные заголовки
        headers.pop('Host', None)
        headers.pop('Content-Length', None)
        
        # Добавляем Content-Type если есть тело запроса
        if request.body:
            headers['Content-Type'] = 'application/json'
        
        logger.debug(f"Заголовки для backend: {headers}")
        
        # Логируем запрос
        logger.info(f"Проксирование запроса: {request.method} {backend_url}")
        logger.debug(f"Заголовки: {headers}")
        if request.body:
            body_text = request.body.decode('utf-8')
            logger.debug(f"Тело запроса: {body_text}")
            logger.debug(f"Размер тела: {len(body_text)} символов")
        
        # Отправляем запрос к backend
        logger.info(f"Отправка запроса к backend...")
        response = requests.request(
            method=request.method,
            url=backend_url,
            headers=headers,
            data=request.body if request.body else None,
            timeout=30
        )
        
        # Логируем ответ
        logger.info(f"Ответ от backend: {response.status_code}")
        logger.debug(f"Заголовки ответа: {dict(response.headers)}")
        logger.debug(f"Тело ответа: {response.text}")
        logger.debug(f"Размер ответа: {len(response.text)} символов")
        
        # Проверяем статус ответа
        if response.status_code >= 200 and response.status_code < 300:
            # Успешный ответ
            try:
                response_data = response.json() if response.content else {}
                logger.info(f"Успешный ответ от backend: {response_data}")
                return JsonResponse(response_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, возвращаем текстовый ответ
                logger.warning(f"Не удалось распарсить JSON ответа: {response.text}")
                return JsonResponse({
                    'success': True,
                    'message': 'Запрос выполнен успешно',
                    'response_text': response.text
                }, status=response.status_code)
        else:
            # Ошибка от backend
            logger.error(f"Ошибка от backend: HTTP {response.status_code}")
            try:
                error_data = response.json() if response.content else {}
                logger.error(f"Данные ошибки: {error_data}")
                return JsonResponse(error_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON ошибки, возвращаем текстовую ошибку
                logger.error(f"Не удалось распарсить JSON ошибки: {response.text}")
                return JsonResponse({
                    'error': 'Ошибка от backend API',
                    'status_code': response.status_code,
                    'response_text': response.text
                }, status=response.status_code)
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут при обращении к backend")
        return JsonResponse({
            'error': 'Backend timeout',
            'status_code': 504
        }, status=504)
        
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка подключения к backend")
        return JsonResponse({
            'error': 'Backend connection error',
            'status_code': 503
        }, status=503)
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'status_code': 500
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_dictionary(request):
    """
    Создает новый справочник
    """
    logger.info(f"=== СОЗДАНИЕ НОВОГО СПРАВОЧНИКА ===")
    logger.info(f"Метод запроса: {request.method}")
    logger.info(f"Заголовки запроса:")
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            logger.info(f"  {key}: {value}")
    
    try:
        # Парсим JSON из тела запроса
        if not request.body:
            logger.error("Отсутствует тело запроса")
            return JsonResponse({
                'error': 'Request body is required',
                'status_code': 400
            }, status=400)
        
        try:
            data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Получены данные: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return JsonResponse({
                'error': 'Invalid JSON format',
                'details': str(e)
            }, status=400)
        
        # Проверяем обязательные поля
        required_fields = ['name', 'code']
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"Отсутствуют обязательные поля: {missing_fields}")
            return JsonResponse({
                'error': 'Missing required fields',
                'missing_fields': missing_fields,
                'status_code': 400
            }, status=400)
        
        # Добавляем значения по умолчанию для отсутствующих полей
        data_with_defaults = data.copy()
        
        # Если не указана, используем сегодняшнюю дату для start_date
        if 'start_date' not in data_with_defaults or not data_with_defaults['start_date']:
            data_with_defaults['start_date'] = date.today().isoformat()
        
        # Если не указан, используем 0 (по умолчанию) для id_type
        if 'id_type' not in data_with_defaults or not data_with_defaults['id_type']:
            data_with_defaults['id_type'] = 0
        
        # Если не указана, используем далекую будущую дату для finish_date
        if 'finish_date' not in data_with_defaults or not data_with_defaults['finish_date']:
            data_with_defaults['finish_date'] = '9999-12-31'
        
        # Если не указано, используем пустую строку для description
        if 'description' not in data_with_defaults or not data_with_defaults['description']:
            data_with_defaults['description'] = ''

        # Убираем поля с пустыми значениями, которые могут вызвать проблемы
        for key in list(data_with_defaults.keys()):
            if data_with_defaults[key] == '' or data_with_defaults[key] is None:
                if key not in ['description', 'name_eng', 'name_bel', 'description_eng', 'description_bel', 'gko', 'organization', 'classifier']:
                    # Для обязательных полей оставляем значения по умолчанию
                    continue
                else:
                    # Для необязательных полей устанавливаем пустую строку
                    data_with_defaults[key] = ''

        # Финальная проверка обязательных полей
        final_required_fields = ['name', 'code', 'start_date', 'finish_date', 'id_type', 'description']
        missing_final_fields = []
        
        for field in final_required_fields:
            if field not in data_with_defaults or not data_with_defaults[field]:
                missing_final_fields.append(field)
        
        if missing_final_fields:
            logger.error(f"После обработки по умолчанию отсутствуют обязательные поля: {missing_final_fields}")
            return JsonResponse({
                'error': 'Failed to prepare required fields',
                'missing_fields': missing_final_fields,
                'processed_data': data_with_defaults
            }, status=400)
        
        logger.info("Все обязательные поля подготовлены успешно")

        # Фильтруем только поля, нужные для схемы DictionaryIn
        allowed_fields = [
            'name', 'code', 'description', 'start_date', 'finish_date',
            'name_eng', 'name_bel', 'description_eng', 'description_bel',
            'gko', 'organization', 'classifier', 'id_type'
        ]
        
        filtered_data = {}
        filtered_out_fields = []
        
        for field in allowed_fields:
            if field in data_with_defaults:
                filtered_data[field] = data_with_defaults[field]
        
        # Логируем поля, которые были отфильтрованы
        for field in data_with_defaults:
            if field not in allowed_fields:
                filtered_out_fields.append(field)
        
        if filtered_out_fields:
            logger.info(f"Отфильтрованы лишние поля: {filtered_out_fields}")
        
        logger.info(f"Данные с дефолтами: {data_with_defaults}")
        logger.info(f"Отфильтрованные данные для backend: {filtered_data}")
        logger.debug(f"Проверка обязательных полей:")
        logger.debug(f"  - start_date: {filtered_data.get('start_date')} (тип: {type(filtered_data.get('start_date'))})")
        logger.debug(f"  - finish_date: {filtered_data.get('finish_date')} (тип: {type(filtered_data.get('finish_date'))})")
        logger.debug(f"  - id_type: {filtered_data.get('id_type')} (тип: {type(filtered_data.get('id_type'))})")
        logger.debug(f"  - description: {filtered_data.get('description')} (тип: {type(filtered_data.get('description'))})")

        # Отправляем запрос к backend
        backend_url = f"{settings.API_DICT['BASE_URL']}/models/newDictionary"
        logger.info(f"URL backend: {backend_url}")
        
        # Получаем токен из заголовка Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        logger.info(f"Заголовок Authorization: {auth_header[:20]}..." if len(auth_header) > 20 else auth_header)
        
        # Отправляем запрос к backend
        logger.info(f"Отправка запроса к backend...")
        response = requests.post(
            url=backend_url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': auth_header
            },
            json=filtered_data, # Используем данные с дефолтами
            timeout=30
        )
        
        # Логируем запрос и ответ
        logger.info(f"Создание словаря: {response.status_code}")
        logger.debug(f"Данные запроса: {filtered_data}") # Логируем данные с дефолтами
        logger.debug(f"URL backend: {backend_url}")
        logger.debug(f"Заголовки запроса: {{'Content-Type': 'application/json', 'Authorization': '{auth_header[:20]}...' if len(auth_header) > 20 else auth_header}}")
        logger.debug(f"Ответ от backend: {response.text}")
        logger.debug(f"Заголовки ответа: {dict(response.headers)}")
        
        # Проверяем статус ответа
        if response.status_code == 200 or response.status_code == 201:
            # Успешный ответ
            try:
                response_data = response.json() if response.content else {}
                logger.info(f"Успешный ответ от backend: {response_data}")
                return JsonResponse(response_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, возвращаем текстовый ответ
                logger.warning(f"Не удалось распарсить JSON ответа: {response.text}")
                return JsonResponse({
                    'success': True,
                    'message': 'Словарь создан успешно',
                    'response_text': response.text
                }, status=response.status_code)
        else:
            # Ошибка от backend
            logger.error(f"Ошибка от backend: HTTP {response.status_code}")
            try:
                error_data = response.json() if response.content else {}
                logger.error(f"Данные ошибки: {error_data}")
                
                # Детальная обработка ошибок валидации
                if response.status_code == 422 and 'detail' in error_data:
                    logger.error("=== ОШИБКА ВАЛИДАЦИИ ОТ BACKEND ===")
                    validation_errors = error_data['detail']
                    
                    for error in validation_errors:
                        logger.error(f"Поле: {'.'.join(str(loc) for loc in error.get('loc', []))}")
                        logger.error(f"Тип ошибки: {error.get('type', 'Неизвестно')}")
                        logger.error(f"Сообщение: {error.get('msg', 'Нет сообщения')}")
                        if 'input' in error:
                            logger.error(f"Входные данные: {error['input']}")
                    
                    # Возвращаем понятную ошибку для пользователя
                    return JsonResponse({
                        'error': 'Ошибка валидации данных',
                        'validation_errors': validation_errors,
                        'status_code': response.status_code,
                        'message': 'Данные не прошли валидацию на backend'
                    }, status=422)
                
                return JsonResponse(error_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON ошибки, возвращаем текстовую ошибку
                logger.error(f"Не удалось распарсить JSON ошибки: {response.text}")
                return JsonResponse({
                    'error': 'Ошибка от backend API',
                    'status_code': response.status_code,
                    'response_text': response.text
                }, status=response.status_code)
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return JsonResponse({
            'error': 'Неверный формат JSON',
            'details': str(e)
        }, status=400)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при создании словаря: {e}")
        return JsonResponse({
            'error': 'Ошибка подключения к backend API',
            'details': str(e)
        }, status=503)
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании словаря: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_dictionary_content(request):
    """
    Получает содержимое справочника
    """
    logger.info(f"=== ПОЛУЧЕНИЕ СОДЕРЖИМОГО СПРАВОЧНИКА ===")
    logger.info(f"Метод запроса: {request.method}")
    logger.info(f"Параметры запроса: {dict(request.GET)}")
    logger.info(f"Все заголовки запроса: {dict(request.META)}")
    logger.info(f"URL запроса: {request.build_absolute_uri()}")
    logger.info(f"Путь запроса: {request.path}")
    logger.info(f"Полный URL: {request.get_full_path()}")
    
    try:
        # Получаем ID справочника из параметров
        dictionary_id = request.GET.get('dictionary')
        if not dictionary_id:
            logger.error("Отсутствует параметр 'dictionary'")
            return JsonResponse({
                'error': 'Missing required parameter: dictionary',
                'status_code': 400
            }, status=400)
        
        logger.info(f"ID справочника: {dictionary_id}")
        
        # Формируем URL для backend
        # Используем прямой URL к FastAPI backend на порту 8000
        # Нужно добавить /api/v2, так как это префикс FastAPI роутера
        backend_url = f"http://127.0.0.1:8000/api/v2/models/dictionary/?dictionary={dictionary_id}"
        logger.info(f"URL backend: {backend_url}")
        
        # Логируем детали запроса для отладки
        logger.info(f"=== ДЕТАЛИ ЗАПРОСА К BACKEND ===")
        logger.info(f"URL: {backend_url}")
        logger.info(f"Метод: GET")
        logger.info(f"Параметр dictionary: {dictionary_id}")
        logger.info(f"Заголовки: {headers}")
        
        # Логируем параметры для отладки
        logger.debug(f"Параметр dictionary: {dictionary_id}")
        logger.debug(f"Тип параметра: {type(dictionary_id)}")
        logger.debug(f"Все GET параметры: {dict(request.GET)}")
        
        # Дополнительная диагностика
        logger.info(f"=== ДИАГНОСТИКА ПАРАМЕТРОВ ===")
        logger.info(f"request.GET.items(): {list(request.GET.items())}")
        logger.info(f"request.GET.get('dictionary'): {request.GET.get('dictionary')}")
        logger.info(f"request.GET.getlist('dictionary'): {request.GET.getlist('dictionary')}")
        
        # Проверяем, что параметр действительно получен
        if not dictionary_id:
            logger.error("Параметр 'dictionary' не найден в запросе!")
            logger.error(f"Все доступные параметры: {dict(request.GET)}")
            return JsonResponse({
                'error': 'Missing required parameter: dictionary',
                'status_code': 400
            }, status=400)
        
        # Логируем детали параметра
        logger.info(f"=== ДЕТАЛИ ПАРАМЕТРА DICTIONARY ===")
        logger.info(f"Значение: {dictionary_id}")
        logger.info(f"Тип: {type(dictionary_id)}")
        logger.info(f"Строковое представление: {repr(dictionary_id)}")
        logger.info(f"Пустой ли: {not dictionary_id}")
        logger.info(f"None ли: {dictionary_id is None}")
        
        # Дополнительная диагностика
        logger.info(f"=== ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА ===")
        logger.info(f"request.GET.items(): {list(request.GET.items())}")
        logger.info(f"request.GET.get('dictionary'): {request.GET.get('dictionary')}")
        logger.info(f"request.GET.getlist('dictionary'): {request.GET.getlist('dictionary')}")
        logger.info(f"request.GET.get('dictionary', 'NOT_FOUND'): {request.GET.get('dictionary', 'NOT_FOUND')}")
        
        # Получаем заголовки авторизации
        headers = {}
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            headers['Authorization'] = auth_header
            logger.info(f"Заголовок авторизации: {auth_header}")
        else:
            logger.warning("Отсутствует заголовок авторизации")
        
        headers['Accept'] = 'application/json'
        
        # Отправляем запрос к backend
        logger.info(f"Отправка запроса к backend...")
        response = requests.get(
            url=backend_url,
            headers=headers,
            timeout=30
        )
        
        # Логируем ответ
        logger.info(f"Ответ от backend: {response.status_code}")
        logger.debug(f"Заголовки ответа: {dict(response.headers)}")
        logger.debug(f"Тело ответа: {response.text}")
        
        # Если есть ошибка, логируем детали
        if response.status_code >= 400:
            logger.error(f"=== ОШИБКА ОТ BACKEND ===")
            logger.error(f"URL: {backend_url}")
            logger.error(f"Статус: {response.status_code}")
            logger.error(f"Заголовки запроса: {headers}")
            logger.error(f"Параметр dictionary: {dictionary_id}")
        
        # Проверяем статус ответа
        if response.status_code >= 200 and response.status_code < 300:
            # Успешный ответ
            try:
                response_data = response.json() if response.content else []
                logger.info(f"Успешно получено содержимое справочника: {len(response_data)} позиций")
                return JsonResponse(response_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить JSON ответа: {response.text}")
                return JsonResponse({
                    'error': 'Invalid JSON response from backend',
                    'response_text': response.text,
                    'status_code': 500
                }, status=500)
        else:
            # Ошибка от backend
            logger.error(f"Ошибка от backend: HTTP {response.status_code}")
            try:
                error_data = response.json() if response.content else {}
                logger.error(f"Данные ошибки: {error_data}")
                return JsonResponse(error_data, status=response.status_code, safe=False)
            except json.JSONDecodeError:
                logger.error(f"Не удалось распарсить JSON ошибки: {response.text}")
                return JsonResponse({
                    'error': 'Backend error',
                    'status_code': response.status_code,
                    'response_text': response.text
                }, status=response.status_code)
                
    except requests.exceptions.Timeout:
        logger.error("Таймаут при обращении к backend")
        return JsonResponse({
            'error': 'Backend timeout',
            'status_code': 504
        }, status=504)
        
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка подключения к backend")
        return JsonResponse({
            'error': 'Backend connection error',
            'status_code': 503
        }, status=503)
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'status_code': 500
        }, status=500)
