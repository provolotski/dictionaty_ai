from django.urls import path
from . import views

urlpatterns =[
    path('login/', views.login_view, name='login'),
    path('login-demo/', views.login_demo_view, name='login_demo'),
    path('logout/', views.logout_view, name='logout'),
    path('audit/', views.audit_view, name='audit'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.users_view, name='users'),
    path('users/<int:user_id>/data/', views.get_user_data_view, name='user_data'),
    path('users/<int:user_id>/update/', views.update_user_view, name='user_update'),
    path('users/<int:user_id>/with-ownership/', views.get_user_with_ownership_view, name='user_with_ownership'),
    path('users/dictionaries/available/', views.get_available_dictionaries_view, name='available_dictionaries'),
    path('users/<int:user_id>/dictionary-ownership/', views.add_dictionary_ownership_view, name='add_dictionary_ownership'),
    path('users/<int:user_id>/dictionary-ownership/<int:dictionary_id>/', views.remove_dictionary_ownership_view, name='remove_dictionary_ownership'),
    path('get_access_token/', views.get_access_token_view, name='get_access_token'),
]