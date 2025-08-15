from django.db import models
from django.utils import timezone


class LoginAudit(models.Model):
    """Модель для аудита попыток входа в систему"""
    
    LOGIN_STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Неудачно'),
        ('blocked', 'Заблокирован'),
    ]
    
    username = models.CharField(max_length=150, verbose_name='Имя пользователя')
    domain = models.CharField(max_length=100, verbose_name='Домен')
    ip_address = models.GenericIPAddressField(verbose_name='IP адрес')
    user_agent = models.TextField(verbose_name='User Agent')
    login_time = models.DateTimeField(default=timezone.now, verbose_name='Время попытки входа')
    status = models.CharField(max_length=20, choices=LOGIN_STATUS_CHOICES, verbose_name='Статус входа')
    error_message = models.TextField(blank=True, null=True, verbose_name='Сообщение об ошибке')
    external_api_response = models.JSONField(blank=True, null=True, verbose_name='Ответ внешнего API')
    
    class Meta:
        db_table = 'login_audit'
        verbose_name = 'Аудит входа'
        verbose_name_plural = 'Аудит входов'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['username', 'login_time']),
            models.Index(fields=['ip_address', 'login_time']),
            models.Index(fields=['status', 'login_time']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.domain}) - {self.status} - {self.login_time}"


class UserGroup(models.Model):
    """Модель для хранения групп пользователей из внешнего API"""
    
    username = models.CharField(max_length=150, verbose_name='Имя пользователя')
    domain = models.CharField(max_length=100, verbose_name='Домен')
    group_name = models.CharField(max_length=200, verbose_name='Название группы')
    last_updated = models.DateTimeField(default=timezone.now, verbose_name='Последнее обновление')
    
    class Meta:
        db_table = 'user_groups'
        verbose_name = 'Группа пользователя'
        verbose_name_plural = 'Группы пользователей'
        unique_together = ['username', 'domain', 'group_name']
        indexes = [
            models.Index(fields=['username', 'domain']),
            models.Index(fields=['group_name']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.domain}) - {self.group_name}"
