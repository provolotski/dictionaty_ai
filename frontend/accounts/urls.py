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
]