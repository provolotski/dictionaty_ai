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
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при проксировании запроса: {e}")
        return JsonResponse({
            'error': 'Ошибка подключения к backend API',
            'details': str(e)
        }, status=503)
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return JsonResponse({
            'error': 'Внутренняя ошибка сервера',
            'details': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_dictionary(request):
    """
    Специальный endpoint для создания словаря
    """
    logger.info(f"=== СОЗДАНИЕ СЛОВАРЯ ЧЕРЕЗ DJANGO API ===")
    logger.info(f"Метод запроса: {request.method}")
    logger.info(f"URL запроса: {request.path}")
    logger.info(f"Заголовки запроса:")
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            logger.info(f"  {key}: {value}")
    
    logger.info(f"Content-Type: {request.META.get('CONTENT_TYPE', 'Не указан')}")
    logger.info(f"Content-Length: {request.META.get('CONTENT_LENGTH', 'Не указан')}")
    
    try:
        # Получаем данные из запроса
        logger.debug(f"Чтение тела запроса...")
        body = request.body.decode('utf-8')
        logger.debug(f"Тело запроса (raw): {body}")
        
        data = json.loads(body)
        logger.info(f"Данные запроса (parsed): {data}")
        logger.debug(f"Тип данных: {type(data)}")
        logger.debug(f"Ключи данных: {list(data.keys())}")
        
        # Валидируем обязательные поля
        required_fields = ['name', 'code']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Отсутствуют обязательные поля: {missing_fields}")
            return JsonResponse({
                'error': 'Отсутствуют обязательные поля',
                'missing_fields': missing_fields,
                'required_fields': required_fields
            }, status=400)
        
        # Проверяем, что данные не пустые
        if not data:
            logger.warning("Получены пустые данные")
            return JsonResponse({
                'error': 'Данные не могут быть пустыми'
            }, status=400)
        
        # Добавляем значения по умолчанию для обязательных полей backend
        from datetime import date
        data_with_defaults = data.copy()
        
        # Если не указана дата начала, используем сегодняшнюю
        if 'start_date' not in data_with_defaults or not data_with_defaults['start_date']:
            data_with_defaults['start_date'] = date.today().isoformat()
        
        # Если не указан тип, используем 0 (по умолчанию)
        if 'id_type' not in data_with_defaults or not data_with_defaults['id_type']:
            data_with_defaults['id_type'] = 0
        
        # Если не указана дата окончания или она пустая/null, используем далекое будущее
        if 'finish_date' not in data_with_defaults or not data_with_defaults['finish_date']:
            data_with_defaults['finish_date'] = '9999-12-31'
        
        # Если не указано описание или оно пустое, используем пустую строку
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
        
        # Фильтруем только те поля, которые нужны для схемы DictionaryIn
        # Убираем поля, которые не должны передаваться к backend
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
        
        logger.info(f"Данные с значениями по умолчанию: {data_with_defaults}")
        logger.info(f"Отфильтрованные данные для backend: {filtered_data}")
        logger.debug(f"Проверка обязательных полей:")
        logger.debug(f"  - start_date: {filtered_data.get('start_date')} (тип: {type(filtered_data.get('start_date'))})")
        logger.debug(f"  - finish_date: {filtered_data.get('finish_date')} (тип: {type(filtered_data.get('finish_date'))})")
        logger.debug(f"  - id_type: {filtered_data.get('id_type')} (тип: {type(filtered_data.get('id_type'))})")
        logger.debug(f"  - description: {filtered_data.get('description')} (тип: {type(filtered_data.get('description'))})")
        
        # Финальная проверка обязательных полей
        final_required_fields = ['name', 'code', 'start_date', 'finish_date', 'id_type', 'description']
        missing_final_fields = []
        
        for field in final_required_fields:
            if field not in filtered_data or not filtered_data[field]:
                missing_final_fields.append(field)
        
        if missing_final_fields:
            logger.error(f"После обработки по умолчанию отсутствуют обязательные поля: {missing_final_fields}")
            return JsonResponse({
                'error': 'Не удалось подготовить обязательные поля',
                'missing_fields': missing_final_fields,
                'processed_data': filtered_data
            }, status=400)
        
        logger.info("Все обязательные поля подготовлены успешно")
        
        # Формируем URL для backend
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
