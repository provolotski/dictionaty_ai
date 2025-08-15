from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('search/', views.search_page, name='search'),
    path('dictionaries/', views.dictionaries_page, name='dictionaries'),
    path('import/', views.import_page, name='import'),
    path('export/', views.export_page, name='export'),
    path('analytics/', views.analytics_page, name='analytics'),
]