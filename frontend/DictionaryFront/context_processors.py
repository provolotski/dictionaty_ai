"""
Context processors for Django templates
"""
from django.conf import settings


def backend_api_url(request):
    """
    Добавляет URL бэкенда в контекст всех шаблонов
    """
    try:
        # Получаем базовый URL из настроек API_DICT
        base_url = getattr(settings, 'API_DICT', {}).get('BASE_URL', 'http://127.0.0.1:8000/api/v2')
        
        # Извлекаем только хост и порт (без /api/v2)
        if base_url.endswith('/api/v2'):
            backend_url = base_url[:-len('/api/v2')]
        elif base_url.endswith('/api/v1'):
            backend_url = base_url[:-len('/api/v1')]
        else:
            # Fallback если структура URL отличается
            backend_url = 'http://127.0.0.1:8000'
        
        return {
            'backend_api_url': backend_url
        }
    except Exception as e:
        # В случае ошибки возвращаем fallback значение
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Ошибка в context processor backend_api_url: {e}")
        
        return {
            'backend_api_url': 'http://127.0.0.1:8000'
        }
