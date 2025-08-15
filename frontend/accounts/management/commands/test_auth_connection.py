from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import time


class Command(BaseCommand):
    help = 'Тестирование подключения к внешнему API авторизации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL для тестирования (по умолчанию из настроек)',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Таймаут в секундах (по умолчанию 30)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ТЕСТ ПОДКЛЮЧЕНИЯ К ВНЕШНЕМУ API ==='))
        
        # Получаем URL для тестирования
        test_url = options['url']
        if not test_url:
            auth_config = getattr(settings, 'AUTH_CONFIG', {})
            if auth_config and auth_config.get('EXTERNAL_API', {}).get('BASE_URL'):
                test_url = auth_config['EXTERNAL_API']['BASE_URL']
            else:
                # Fallback на старые настройки
                test_url = getattr(settings, 'API_OATH', {}).get('BASE_URL')
        
        if not test_url:
            self.stdout.write(self.style.ERROR('❌ URL для тестирования не найден в настройках'))
            return
        
        timeout = options['timeout']
        verbose = options['verbose']
        
        self.stdout.write(f"URL для тестирования: {test_url}")
        self.stdout.write(f"Таймаут: {timeout} сек")
        self.stdout.write("")
        
        # Тест 1: Проверка доступности сервера
        self.stdout.write("1. Проверка доступности сервера...")
        try:
            # Убираем протокол и путь для ping-теста
            import urllib.parse
            parsed = urllib.parse.urlparse(test_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            self.stdout.write(f"   Хост: {host}")
            self.stdout.write(f"   Порт: {port}")
            
            # Простой тест TCP соединения
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.stdout.write(self.style.SUCCESS("   ✅ Сервер доступен"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ Сервер недоступен (код ошибки: {result})"))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка проверки сервера: {e}"))
            return
        
        # Тест 2: HTTP GET запрос
        self.stdout.write("2. HTTP GET запрос...")
        try:
            start_time = time.time()
            response = requests.get(test_url, timeout=timeout)
            response_time = time.time() - start_time
            
            self.stdout.write(f"   Статус: {response.status_code}")
            self.stdout.write(f"   Время ответа: {response_time:.2f} сек")
            self.stdout.write(f"   Размер ответа: {len(response.content)} байт")
            
            if verbose:
                self.stdout.write(f"   Заголовки: {dict(response.headers)}")
                if response.content:
                    self.stdout.write(f"   Содержимое: {response.text[:500]}...")
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("   ✅ HTTP GET успешен"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  HTTP GET вернул статус {response.status_code}"))
                
        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR(f"   ❌ Таймаут ({timeout} сек)"))
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка соединения: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка HTTP GET: {e}"))
        
        # Тест 3: POST запрос на /login
        self.stdout.write("3. POST запрос на /login...")
        try:
            login_url = f"{test_url}/login"
            test_data = {
                'username': 'test_user',
                'password': 'test_password',
                'domain': 'test_domain'
            }
            
            self.stdout.write(f"   URL: {login_url}")
            self.stdout.write(f"   Тестовые данные: {test_data}")
            
            start_time = time.time()
            response = requests.post(
                login_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            self.stdout.write(f"   Статус: {response.status_code}")
            self.stdout.write(f"   Время ответа: {response_time:.2f} сек")
            self.stdout.write(f"   Размер ответа: {len(response.content)} байт")
            
            if verbose:
                self.stdout.write(f"   Заголовки: {dict(response.headers)}")
                if response.content:
                    try:
                        response_json = response.json()
                        self.stdout.write(f"   JSON ответ: {response_json}")
                    except:
                        self.stdout.write(f"   Текстовый ответ: {response.text[:500]}...")
            
            if response.status_code in [400, 401, 403]:
                self.stdout.write(self.style.SUCCESS("   ✅ API отвечает (ожидаемая ошибка аутентификации)"))
            elif response.status_code == 200:
                self.stdout.write(self.style.WARNING("   ⚠️  API принял тестовые учетные данные (неожиданно)"))
            elif response.status_code == 404:
                self.stdout.write(self.style.ERROR("   ❌ Endpoint /login не найден"))
            elif response.status_code >= 500:
                self.stdout.write(self.style.ERROR(f"   ❌ Серверная ошибка: {response.status_code}"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  Неожиданный статус: {response.status_code}"))
                
        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR(f"   ❌ Таймаут ({timeout} сек)"))
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка соединения: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка POST запроса: {e}"))
        
        # Тест 4: Проверка через auth_manager
        self.stdout.write("4. Тест через auth_manager...")
        try:
            from accounts.auth_manager import auth_manager
            
            self.stdout.write(f"   Внешний API включен: {auth_manager.external_api_enabled}")
            self.stdout.write(f"   Внешний API настроен: {auth_manager.external_api_config.get('ENABLED', False)}")
            self.stdout.write(f"   Base URL: {auth_manager.external_api_config.get('BASE_URL', 'Не настроен')}")
            
            # Проверяем доступность через auth_manager
            if auth_manager.external_api_enabled and auth_manager.external_api_config.get('ENABLED', False):
                available = auth_manager.is_external_api_available()
                self.stdout.write(f"   Доступность API: {'✅ Доступен' if available else '❌ Недоступен'}")
            else:
                self.stdout.write("   ⚠️  Внешний API отключен в настройках")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Ошибка тестирования auth_manager: {e}"))
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ==="))
        
        # Рекомендации
        self.stdout.write("")
        self.stdout.write("=== РЕКОМЕНДАЦИИ ===")
        
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        if not auth_config:
            self.stdout.write("❌ AUTH_CONFIG не настроен в settings.py")
            self.stdout.write("   Добавьте настройки авторизации")
        else:
            if auth_config.get('USE_EXTERNAL_API', False):
                self.stdout.write("✅ Внешний API включен")
                if not auth_config.get('LOCAL_AUTH', {}).get('FALLBACK', False):
                    self.stdout.write("⚠️  Рекомендуется включить fallback на локальную авторизацию")
            else:
                self.stdout.write("✅ Локальная авторизация включена")
        
        self.stdout.write("")
        self.stdout.write("Для изменения настроек используйте:")
        self.stdout.write("  python manage.py configure_auth --show")
        self.stdout.write("  python manage.py configure_auth --local-auth")
        self.stdout.write("  python manage.py configure_auth --external-api --fallback")
