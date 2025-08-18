from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from pydantic import ValidationError
import requests
import json
import logging

from .models import Dictionary, DictionaryIn
from .forms import DictionaryForm
from accounts.utils import api_get, api_post, api_post_create_dict,api_post_dict

logger = logging.getLogger('myapp')


def require_users_group(view_func):
    """Декоратор для проверки принадлежности к группе EISGS_Users"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('in_users', False):
            messages.error(request, 'У Вас недостаточно прав для доступа к этой странице')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@require_http_methods(["GET"])
@require_users_group
def dictionary_list_view(request):
    """Список справочников"""
    # Проверяем, входит ли пользователь в группу EISGS_Users
    if not request.session.get('in_users', False):
        messages.error(request, 'У Вас недостаточно прав для доступа к справочникам')
        return redirect('home')
    
    try:
        logger.debug('dictionary_list_view')
        response = api_get(request, '/models/list', service='dict')
        dictionaries = response.json() if response.status_code == 200 else []
    except requests.RequestException as e:
        logger.error(f'Ошибка API: {e}')
        dictionaries = []
        messages.error(request, 'Ошибка загрузки списка справочников')

    logger.debug(f'Загружено справочников: {len(dictionaries)}')
    return render(request, 'dictionaryList.html', {'dictionaries': dictionaries})


@require_users_group
def dictionary_create(request):
    """Создание справочника"""
    if request.method == 'POST':
        form = DictionaryForm(request.POST)
        if form.is_valid():
            try:
                dictionary = form.cleaned_data

                # Преобразуем даты в ISO формат
                if 'start_date' in dictionary and dictionary['start_date']:
                    dictionary['start_date'] = dictionary['start_date'].isoformat()
                if 'finish_date' in dictionary and dictionary['finish_date']:
                    dictionary['finish_date'] = dictionary['finish_date'].isoformat()

                # Валидируем данные через Pydantic
                dictionary_base = DictionaryIn.model_validate(dictionary)

                # Отправляем на API
                response = api_post_create_dict('/models/newDictionary', data=dictionary_base)

                if response.status_code in [200, 201]:
                    success_msg = f'Справочник "{dictionary["name"]}" создан успешно!'

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': success_msg,
                            'data': dictionary
                        })
                    messages.success(request, success_msg)
                    return redirect('dictionary_list')
                else:
                    error_msg = f'Ошибка API: {response.text}'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)

            except ValidationError as e:
                error_msg = f'Ошибка валидации: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)

            except requests.RequestException as e:
                error_msg = f'Ошибка соединения: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            messages.error(request, 'Ошибка валидации формы')
    else:
        form = DictionaryForm()

    # Для AJAX возвращаем форму в модальном окне
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'dictionaries/form_modal.html', {
            'form': form,
            'dictionary_id': None
        })

    return render(request, 'dictionaries/form_modal.html', {'form': form})


@require_users_group
def dictionary_edit(request, pk):
    """Редактирование существующего справочника"""
    logger.debug(f'dictionary_edit pk={pk}')

    # Получаем данные справочника из API
    response = api_get(request, f'/models/getMetaDictionary?dictionary_id={pk}', service='dict')
    if response.status_code != 200:
        error_msg = 'Справочник не найден'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        return redirect('dictionary_list')

    dictionary_data = response.json()

    if request.method == 'POST':
        form = DictionaryForm(request.POST)
        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                # Преобразуем даты в ISO формат
                if 'start_date' in cleaned_data and cleaned_data['start_date']:
                    cleaned_data['start_date'] = cleaned_data['start_date'].isoformat()
                if 'finish_date' in cleaned_data and cleaned_data['finish_date']:
                    cleaned_data['finish_date'] = cleaned_data['finish_date'].isoformat()

                # Отправляем обновленные данные в API
                response = api_post_dict(f'/models/EditDictionary?dictionary_id={pk}',
                                    data=cleaned_data, service='dict')

                if response.status_code in [200, 201]:
                    success_msg = f'Справочник "{cleaned_data["name"]}" обновлен успешно!'

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': success_msg,
                            'data': cleaned_data
                        })

                    messages.success(request, success_msg)
                    return redirect('dictionary_list')
                else:
                    error_msg = f'Ошибка при обновлении: {response.text}'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)

            except requests.RequestException as e:
                error_msg = f'Ошибка соединения: {str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            messages.error(request, 'Ошибка валидации формы')
    else:
        # Предзаполняем форму данными из API
        form = DictionaryForm(initial=dictionary_data)

    # Для AJAX возвращаем форму в модальном окне
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'dictionaries/form_modal.html', {
            'form': form,
            'dictionary_id': pk,
            'dictionary_data': dictionary_data
        })

    return render(request, 'dictionaries/edit.html', {
        'form': form,
        'dictionary_id': pk,
        'dictionary_data': dictionary_data
    })


@require_users_group
def dictionary_delete(request, pk):
    """Удаление справочника"""
    if request.method == 'POST':
        try:
            response = api_post(request, f'/models/deleteDictionary?dictionary_id={pk}', service='dict')

            if response.status_code in [200, 201, 204]:
                success_msg = 'Справочник успешно удален'

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': success_msg
                    })

                messages.success(request, success_msg)
            else:
                error_msg = f'Ошибка при удалении: {response.text}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)

        except requests.RequestException as e:
            error_msg = f'Ошибка соединения: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

    return redirect('dictionary_list')


@require_users_group
def dictionary_detail_view(request, dictionary_id):
    """Детальный просмотр справочника"""
    try:
        response = api_post(request, f'/models/dictionary/?dictionary={dictionary_id}', service='dict')
        data = response.json() if response.status_code == 200 else {}

        processed_items = []
        for item in data:
            processed = {
                'id': item['id'],
                'parent_id': item['parent_id'],
                'code': next((attr['value'] for attr in item['attrs'] if attr['name'] == 'Код'), ''),
                'name': next((attr['value'] for attr in item['attrs'] if attr['name'] == 'Наименование'), ''),
                'children': []
            }
            processed_items.append(processed)

        # Строим дерево
        tree = build_tree(processed_items)

        return render(request, 'tree.html', {
            'tree': tree,
            'tree_json': json.dumps(tree, cls=DjangoJSONEncoder)
        })
    except requests.RequestException as e:
        logger.error(f'Ошибка загрузки деталей справочника: {e}')
        messages.error(request, 'Ошибка загрузки справочника')
        return redirect('dictionary_list')


def build_tree(items, parent_id=None):
    """Построение дерева из элементов"""
    branch = []
    for item in items:
        if item['parent_id'] == parent_id:
            children = build_tree(items, item['id'])
            if children:
                item['children'] = children
            branch.append(item)
    return branch


@require_POST
@require_users_group
def sync_dictionaries(request):
    """Синхронизация справочников"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        from .services import DictionaryAPIClient
        success = DictionaryAPIClient.sync_dictionaries()
        return JsonResponse({'success': success})
    except Exception as e:
        logger.error(f'Ошибка синхронизации: {e}')
        return JsonResponse({'success': False, 'error': str(e)})


@require_users_group
def save_dictionary_view(request):
    """Сохранение справочника (устаревшая функция)"""
    return redirect('dictionary_list')


@require_users_group
def api_dictionary_list(request):
    """API endpoint для получения списка справочников из внешнего API"""
    try:
        # Используем внешний API_DICT для получения списка справочников
        response = api_get(request, '/models/list', service='dict')
        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'error': 'Failed to fetch dictionaries from external API'}, status=response.status_code)
    except requests.RequestException as e:
        logger.error(f'External API Error in dictionary_list: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_users_group
def api_dictionary_detail(request, dictionary_id):
    """API endpoint для получения детальной информации о справочнике из внешнего API"""
    try:
        # Используем внешний API_DICT для получения деталей справочника
        response = api_get(request, f'/models/dictionary/?dictionary={dictionary_id}', service='dict')
        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'error': 'Failed to fetch dictionary details from external API'}, status=response.status_code)
    except requests.RequestException as e:
        logger.error(f'External API Error in dictionary_detail: {e}')
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_users_group
def api_dictionary_paginated(request, dictionary_id):
    """API endpoint для получения данных справочника с пагинацией"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Ограничиваем размер страницы для производительности
        if page_size > 200:
            page_size = 200
        elif page_size < 10:
            page_size = 10
        
        # Ключ кэша
        cache_key = f'dictionary_data_{dictionary_id}'
        cache_timeout = 300  # 5 минут
        
        # Пытаемся получить данные из кэша
        processed_data = cache.get(cache_key)
        
        if processed_data is None:
            # Получаем данные справочника из внешнего API
            response = api_get(request, f'/models/dictionary/?dictionary={dictionary_id}', service='dict')
            if response.status_code == 200:
                data = response.json()
                
                # Обрабатываем данные
                processed_data = []
                for item in data:
                    processed_item = {
                        'id': item['id'],
                        'parent_id': item['parent_id'],
                        'parent_code': item.get('parent_code'),
                    }
                    
                    # Извлекаем атрибуты
                    for attr in item['attrs']:
                        attr_name = attr['name']
                        attr_value = attr['value']
                        processed_item[attr_name] = attr_value
                    
                    processed_data.append(processed_item)
                
                # Сохраняем в кэш
                cache.set(cache_key, processed_data, cache_timeout)
            else:
                return JsonResponse({'error': 'Ошибка получения данных'}, status=400)
        
        # Пагинация
        paginator = Paginator(processed_data, page_size)
        page_obj = paginator.get_page(page)
        
        # Подготавливаем данные для ответа
        result = {
            'items': list(page_obj),
            'total_items': len(processed_data),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        
        return JsonResponse(result)
        
    except (ValueError, requests.RequestException) as e:
        logger.error(f'Ошибка API запроса: {e}')
        return JsonResponse({'error': 'Ошибка обработки запроса'}, status=500)


@require_users_group
def dictionary_table_view(request, dictionary_id):
    """Отображение справочника в виде таблицы с пагинацией и кэшированием"""
    try:
        # Ключи кэша
        cache_key_data = f'dictionary_data_{dictionary_id}'
        cache_key_meta = f'dictionary_meta_{dictionary_id}'
        cache_timeout = 300  # 5 минут
        
        # Пытаемся получить данные из кэша
        processed_data = cache.get(cache_key_data)
        dictionary_name = cache.get(cache_key_meta)
        
        if processed_data is None or dictionary_name is None:
            # Получаем данные справочника из внешнего API
            response = api_get(request, f'/models/dictionary/?dictionary={dictionary_id}', service='dict')
            if response.status_code == 200:
                data = response.json()
                
                # Получаем метаданные справочника для заголовка
                meta_response = api_get(request, f'/models/getMetaDictionary?dictionary_id={dictionary_id}', service='dict')
                dictionary_name = "Справочник"
                if meta_response.status_code == 200:
                    meta_data = meta_response.json()
                    dictionary_name = meta_data.get('name', 'Справочник')
                
                # Обрабатываем данные для отображения в таблице
                processed_data = []
                for item in data:
                    processed_item = {
                        'id': item['id'],
                        'parent_id': item['parent_id'],
                        'parent_code': item.get('parent_code'),
                    }
                    
                    # Извлекаем атрибуты
                    for attr in item['attrs']:
                        attr_name = attr['name']
                        attr_value = attr['value']
                        processed_item[attr_name] = attr_value
                    
                    processed_data.append(processed_item)
                
                # Сохраняем в кэш
                cache.set(cache_key_data, processed_data, cache_timeout)
                cache.set(cache_key_meta, dictionary_name, cache_timeout)
            else:
                messages.error(request, 'Ошибка загрузки справочника')
                return redirect('dictionary_list')
        
        # Пагинация
        page_number = request.GET.get('page', 1)
        items_per_page = int(request.GET.get('page_size', 50))  # Количество элементов на странице
        
        # Ограничиваем размер страницы для производительности
        if items_per_page > 200:
            items_per_page = 200
        elif items_per_page < 10:
            items_per_page = 10
        
        paginator = Paginator(processed_data, items_per_page)
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'dictionaryTable.html', {
            'dictionary_name': dictionary_name,
            'dictionary_id': dictionary_id,
            'items': page_obj,
            'total_items': len(processed_data),
            'page_obj': page_obj,
            'paginator': paginator,
            'current_page_size': items_per_page
        })
            
    except requests.RequestException as e:
        logger.error(f'Ошибка загрузки справочника: {e}')
        messages.error(request, 'Ошибка загрузки справочника')
        return redirect('dictionary_list')


@require_users_group
def dictionary_tree_view(request, dictionary_id):
    """Отображение справочника в виде дерева"""
    try:
        # Получаем данные справочника из внешнего API
        response = api_get(request, f'/models/dictionary/?dictionary={dictionary_id}', service='dict')
        if response.status_code == 200:
            data = response.json()
            
            # Получаем метаданные справочника для заголовка
            meta_response = api_get(request, f'/models/getMetaDictionary?dictionary_id={dictionary_id}', service='dict')
            dictionary_name = "Справочник"
            if meta_response.status_code == 200:
                meta_data = meta_response.json()
                dictionary_name = meta_data.get('name', 'Справочник')
            
            # Строим дерево из данных
            tree_data = build_tree_from_data(data)
            
            return render(request, 'dictionaryTree.html', {
                'dictionary_name': dictionary_name,
                'dictionary_id': dictionary_id,
                'tree_data': tree_data,
                'total_items': len(data)
            })
        else:
            messages.error(request, 'Ошибка загрузки справочника')
            return redirect('dictionary_list')
            
    except requests.RequestException as e:
        logger.error(f'Ошибка загрузки справочника: {e}')
        messages.error(request, 'Ошибка загрузки справочника')
        return redirect('dictionary_list')


def build_tree_from_data(data):
    """Строит дерево из данных справочника"""
    # Создаем словарь для быстрого поиска по ID
    items_dict = {}
    root_items = []
    
    # Первый проход: создаем словарь всех элементов
    for item in data:
        item_id = item['id']
        processed_item = {
            'id': item_id,
            'parent_id': item['parent_id'],
            'parent_code': item.get('parent_code'),
            'children': [],
            'level': 0
        }
        
        # Извлекаем атрибуты
        for attr in item['attrs']:
            attr_name = attr['name']
            attr_value = attr['value']
            processed_item[attr_name] = attr_value
        
        items_dict[item_id] = processed_item
    
    # Второй проход: строим иерархию
    for item_id, item in items_dict.items():
        parent_id = item['parent_id']
        
        if parent_id is None:
            # Корневой элемент
            root_items.append(item)
        else:
            # Дочерний элемент
            if parent_id in items_dict:
                parent = items_dict[parent_id]
                parent['children'].append(item)
                item['level'] = parent['level'] + 1
    
    return root_items