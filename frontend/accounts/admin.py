from django.contrib import admin
from .models import LoginAudit, UserGroup


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    """Админка для аудита логинов"""
    
    list_display = ['username', 'domain', 'ip_address', 'status', 'login_time']
    list_filter = ['status', 'domain', 'login_time']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['username', 'domain', 'ip_address', 'user_agent', 'login_time', 'status', 'error_message', 'external_api_response']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'domain', 'status', 'login_time')
        }),
        ('Сетевая информация', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Детали', {
            'fields': ('error_message', 'external_api_response'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Запрещаем создание записей вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение записей"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление только суперпользователям"""
        return request.user.is_superuser


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    """Админка для групп пользователей"""
    
    list_display = ['username', 'domain', 'group_name', 'last_updated']
    list_filter = ['domain', 'group_name', 'last_updated']
    search_fields = ['username', 'group_name']
    readonly_fields = ['username', 'domain', 'group_name', 'last_updated']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'domain', 'group_name')
        }),
        ('Метаданные', {
            'fields': ('last_updated',)
        }),
    )
    
    def has_add_permission(self, request):
        """Запрещаем создание записей вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение записей"""
        return False
