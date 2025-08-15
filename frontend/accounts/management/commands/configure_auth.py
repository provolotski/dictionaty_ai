from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import json
import os


class Command(BaseCommand):
    help = 'Настройка конфигурации авторизации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--external-api',
            action='store_true',
            help='Включить внешний API авторизации',
        )
        parser.add_argument(
            '--local-auth',
            action='store_true',
            help='Включить только локальную авторизацию',
        )
        parser.add_argument(
            '--fallback',
            action='store_true',
            help='Включить fallback на локальную авторизацию',
        )
        parser.add_argument(
            '--external-url',
            type=str,
            help='URL внешнего API авторизации',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            help='Таймаут для внешнего API (в секундах)',
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='Показать текущую конфигурацию',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Сбросить к настройкам по умолчанию',
        )

    def handle(self, *args, **options):
        settings_file = os.path.join(settings.BASE_DIR, 'DictionaryFront', 'settings.py')
        
        if options['show']:
            self.show_current_config()
            return
        
        if options['reset']:
            self.reset_to_default(settings_file)
            return
        
        # Читаем текущие настройки
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise CommandError(f"Файл настроек не найден: {settings_file}")
        
        # Обновляем настройки
        if options['external_api']:
            content = self.update_external_api_config(content, True)
            self.stdout.write(self.style.SUCCESS('Внешний API авторизации включен'))
        
        if options['local_auth']:
            content = self.update_external_api_config(content, False)
            self.stdout.write(self.style.SUCCESS('Локальная авторизация включена'))
        
        if options['fallback']:
            content = self.update_fallback_config(content, True)
            self.stdout.write(self.style.SUCCESS('Fallback на локальную авторизацию включен'))
        
        if options['external_url']:
            content = self.update_external_url(content, options['external_url'])
            self.stdout.write(self.style.SUCCESS(f'URL внешнего API обновлен: {options["external_url"]}'))
        
        if options['timeout']:
            content = self.update_timeout(content, options['timeout'])
            self.stdout.write(self.style.SUCCESS(f'Таймаут обновлен: {options["timeout"]} сек'))
        
        # Записываем обновленные настройки
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stdout.write(self.style.SUCCESS('Настройки успешно обновлены'))
        except Exception as e:
            raise CommandError(f"Ошибка при записи файла настроек: {e}")
    
    def show_current_config(self):
        """Показать текущую конфигурацию"""
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        
        self.stdout.write(self.style.SUCCESS('Текущая конфигурация авторизации:'))
        self.stdout.write(f"  Внешний API: {'ВКЛ' if auth_config.get('USE_EXTERNAL_API', True) else 'ВЫКЛ'}")
        self.stdout.write(f"  Локальная авторизация: {'ВКЛ' if auth_config.get('LOCAL_AUTH', {}).get('ENABLED', True) else 'ВЫКЛ'}")
        self.stdout.write(f"  Fallback: {'ВКЛ' if auth_config.get('LOCAL_AUTH', {}).get('FALLBACK', True) else 'ВЫКЛ'}")
        
        external_config = auth_config.get('EXTERNAL_API', {})
        self.stdout.write(f"  URL внешнего API: {external_config.get('BASE_URL', 'Не настроен')}")
        self.stdout.write(f"  Таймаут: {external_config.get('TIMEOUT', 30)} сек")
        self.stdout.write(f"  Попытки повтора: {external_config.get('RETRY_ATTEMPTS', 3)}")
    
    def reset_to_default(self, settings_file):
        """Сбросить к настройкам по умолчанию"""
        default_config = '''# Настройки авторизации
AUTH_CONFIG = {
    'USE_EXTERNAL_API': True,  # True - использовать внешний API, False - локальную авторизацию
    'EXTERNAL_API': {
        'BASE_URL': 'http://172.16.251.170:9090/api/v1/auth',
        'ENABLED': True,
        'TIMEOUT': 30,
        'RETRY_ATTEMPTS': 3,
    },
    'LOCAL_AUTH': {
        'ENABLED': True,
        'FALLBACK': True,  # Использовать как fallback при недоступности внешнего API
    }
}'''
        
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Заменяем существующую конфигурацию
            import re
            pattern = r'# Настройки авторизации\s*AUTH_CONFIG\s*=\s*\{[^}]*\}'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, default_config, content, flags=re.DOTALL)
            else:
                # Если конфигурация не найдена, добавляем в конец
                content += f"\n\n{default_config}"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.stdout.write(self.style.SUCCESS('Настройки сброшены к значениям по умолчанию'))
            
        except Exception as e:
            raise CommandError(f"Ошибка при сбросе настроек: {e}")
    
    def update_external_api_config(self, content, enabled):
        """Обновить настройку внешнего API"""
        import re
        pattern = r"('USE_EXTERNAL_API':\s*)(True|False)"
        replacement = r"\1" + str(enabled)
        return re.sub(pattern, replacement, content)
    
    def update_fallback_config(self, content, enabled):
        """Обновить настройку fallback"""
        import re
        pattern = r"('FALLBACK':\s*)(True|False)"
        replacement = r"\1" + str(enabled)
        return re.sub(pattern, replacement, content)
    
    def update_external_url(self, content, url):
        """Обновить URL внешнего API"""
        import re
        pattern = r"('BASE_URL':\s*')([^']*)(')"
        replacement = r"\1" + url + r"\3"
        return re.sub(pattern, replacement, content)
    
    def update_timeout(self, content, timeout):
        """Обновить таймаут"""
        import re
        pattern = r"('TIMEOUT':\s*)(\d+)"
        replacement = r"\1" + str(timeout)
        return re.sub(pattern, replacement, content)
