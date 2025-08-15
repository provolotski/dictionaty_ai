from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import LoginAudit, UserGroup
from datetime import timedelta


class Command(BaseCommand):
    help = 'Просмотр аудита логинов в систему'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Количество дней для просмотра (по умолчанию 7)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Фильтр по имени пользователя'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['success', 'failed', 'blocked'],
            help='Фильтр по статусу входа'
        )
        parser.add_argument(
            '--show-groups',
            action='store_true',
            help='Показать информацию о группах пользователей'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        username_filter = options['username']
        status_filter = options['status']
        show_groups = options['show_groups']
        
        # Вычисляем дату начала периода
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Аудит логинов за последние {days} дней")
        self.stdout.write("=" * 60)
        
        # Получаем записи аудита
        audit_queryset = LoginAudit.objects.filter(login_time__gte=start_date)
        
        if username_filter:
            audit_queryset = audit_queryset.filter(username__icontains=username_filter)
            self.stdout.write(f"Фильтр по пользователю: {username_filter}")
        
        if status_filter:
            audit_queryset = audit_queryset.filter(status=status_filter)
            self.stdout.write(f"Фильтр по статусу: {status_filter}")
        
        # Статистика
        total_attempts = audit_queryset.count()
        successful_logins = audit_queryset.filter(status='success').count()
        failed_logins = audit_queryset.filter(status='failed').count()
        blocked_logins = audit_queryset.filter(status='blocked').count()
        
        self.stdout.write(f"Общее количество попыток: {total_attempts}")
        self.stdout.write(f"Успешных входов: {successful_logins}")
        self.stdout.write(f"Неудачных попыток: {failed_logins}")
        self.stdout.write(f"Заблокированных: {blocked_logins}")
        self.stdout.write("")
        
        # Детальный список
        if total_attempts > 0:
            self.stdout.write("Детальный список:")
            self.stdout.write("-" * 60)
            
            for audit in audit_queryset.order_by('-login_time')[:20]:  # Показываем последние 20
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'blocked': '🚫'
                }.get(audit.status, '❓')
                
                self.stdout.write(
                    f"{status_icon} {audit.username}@{audit.domain} "
                    f"({audit.ip_address}) - {audit.login_time.strftime('%d.%m.%Y %H:%M:%S')}"
                )
                
                if audit.error_message:
                    self.stdout.write(f"    Ошибка: {audit.error_message}")
        
        # Информация о группах пользователей
        if show_groups:
            self.stdout.write("")
            self.stdout.write("Информация о группах пользователей:")
            self.stdout.write("-" * 60)
            
            groups_queryset = UserGroup.objects.all()
            if username_filter:
                groups_queryset = groups_queryset.filter(username__icontains=username_filter)
            
            for group in groups_queryset.order_by('username', 'domain'):
                self.stdout.write(
                    f"👤 {group.username}@{group.domain} - {group.group_name} "
                    f"(обновлено: {group.last_updated.strftime('%d.%m.%Y %H:%M:%S')})"
                )
        
        if total_attempts == 0:
            self.stdout.write(self.style.WARNING("Записи аудита не найдены"))
