from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.permissions import check_user_access


class Command(BaseCommand):
    help = 'Тестирование проверки прав доступа пользователей'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('domain', type=str, help='Домен пользователя')
    
    def handle(self, *args, **options):
        username = options['username']
        domain = options['domain']
        
        self.stdout.write(f"Тестирование прав доступа для {username}@{domain}")
        self.stdout.write("=" * 50)
        
        # Проверяем конфигурацию
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        self.stdout.write(f"Конфигурация AUTH_CONFIG: {auth_config}")
        
        # Тестируем проверку прав
        try:
            # Для тестирования нужен access_token, но мы можем протестировать только структуру
            self.stdout.write("⚠️  Для полного тестирования нужен access_token")
            self.stdout.write("Тестируем только структуру функции...")
            
            # Создаем тестовый токен (недействительный)
            test_token = "test_token_for_testing"
            
            result = check_user_access(username, domain, test_token)
            
            self.stdout.write(f"Результат проверки:")
            self.stdout.write(f"  - Доступ: {'✅ Есть' if result['has_access'] else '❌ Нет'}")
            self.stdout.write(f"  - Группы: {result['groups']}")
            
            if result['error_message']:
                self.stdout.write(f"  - Ошибка: {result['error_message']}")
            
            if result['has_access']:
                self.stdout.write(self.style.SUCCESS("Пользователь имеет доступ к системе"))
            else:
                self.stdout.write(self.style.ERROR("Пользователь не имеет доступа к системе"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при проверке прав: {e}"))
            self.stdout.write("Traceback:", exc_info=True)
