from django.urls import path

# from accounts.urls import urlpatterns
from . import views



urlpatterns =[
    path('list/', views.dictionary_list_view, name='dictionary_list'),
    path('create/', views.dictionary_create, name='dictionary_create'),
    path('<int:dictionary_id>/', views.dictionary_detail_view, name='dictionary_detail'),
    path('<int:dictionary_id>/detail/', views.dictionary_detail_view, name='dictionary_detail'),
    path('<int:dictionary_id>/description/', views.dictionary_description_view, name='dictionary_description'),
    path('<int:dictionary_id>/view/', views.dictionary_view_view, name='dictionary_view'),
    path('<int:dictionary_id>/table/', views.dictionary_table_view, name='dictionary_table'),
    path('<int:dictionary_id>/tree/', views.dictionary_tree_view, name='dictionary_tree'),
    path('<int:pk>/edit/', views.dictionary_edit, name='dictionary_edit'),
    path('<int:pk>/edit-description/', views.dictionary_edit_description, name='dictionary_edit_description'),
    path('<int:pk>/view-modal/', views.dictionary_view_modal, name='dictionary_view_modal'),
    path('<int:pk>/test-description/', views.test_description_url, name='test_description_url'),
    path('<int:pk>/delete/', views.dictionary_delete, name='dictionary_delete'),
    path('save/', views.save_dictionary_view, name='save_dictionary'),
    path('sync/', views.sync_dictionaries, name='sync_dictionaries'),
    
    # API endpoints
    path('api/v2/models/dictionary/', views.api_dictionary_list, name='api_dictionary_list'),
    path('api/v2/models/dictionary/<int:dictionary_id>/', views.api_dictionary_detail, name='api_dictionary_detail'),
    path('api/v2/models/dictionary/<int:dictionary_id>/paginated/', views.api_dictionary_paginated, name='api_dictionary_paginated'),
]