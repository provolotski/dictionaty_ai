"""
URL маршруты для API прокси
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Прокси для всех API запросов
    path('v2/<path:path>', views.proxy_api_request, name='proxy_api'),
    
    # Специальный endpoint для создания словаря
    path('v2/models/newDictionary', views.create_dictionary, name='create_dictionary'),
]
