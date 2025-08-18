from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages


def require_users_group(view_func):
    """Декоратор для проверки принадлежности к группе EISGS_Users"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('in_users', False):
            messages.error(request, 'У Вас недостаточно прав для доступа к этой странице')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def home_page(request):
    return render(request, 'home.html')

@require_users_group
def search_page(request):
    return render(request, 'search.html')

@require_users_group
def dictionaries_page(request):
    """Страница со списком словарей"""
    try:
        from accounts.utils import api_get
        
        # Получаем список словарей с backend API
        response = api_get(request, '/models/list', service='dict')
        
        if response and response.status_code == 200:
            dictionaries = response.json()
        else:
            dictionaries = []
            if response:
                messages.error(request, f'Ошибка получения словарей: {response.status_code}')
            else:
                messages.error(request, 'Ошибка подключения к backend API')
                
    except Exception as e:
        dictionaries = []
        messages.error(request, f'Ошибка при получении словарей: {str(e)}')
    
    context = {
        'dictionaries': dictionaries,
        'total_count': len(dictionaries) if isinstance(dictionaries, list) else 0
    }
    
    return render(request, 'dictionaries.html', context)

@require_users_group
def dictionary_create_page(request):
    """Страница создания нового словаря"""
    # Получаем токен из сессии
    access_token = request.session.get('access_token', '')
    
    context = {
        'access_token': access_token
    }
    
    return render(request, 'dictionary_create.html', context)

@require_users_group
def import_page(request):
    return render(request, 'import.html')

@require_users_group
def export_page(request):
    return render(request, 'export.html')

@require_users_group
def analytics_page(request):
    return render(request, 'analytics.html')