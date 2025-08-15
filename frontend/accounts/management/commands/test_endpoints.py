from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json

class Command(BaseCommand):
    help = 'Тестирует различные endpoints API для поиска правильного'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('password', type=str, help='Пароль')
        parser.add_argument('domain', type=str, help='Домен')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        domain = options['domain']
        
        self.stdout.write(f"Тестирование endpoints API для {username}@{domain}")
        self.stdout.write("=" * 70)
        
        # Получаем токены
        auth_url = f"{settings.AUTH_CONFIG['EXTERNAL_API']['BASE_URL']}/login"
        auth_data = {
            'username': username,
            'password': password,
            'domain': domain
        }
        
        try:
            # Аутентификация
            self.stdout.write("🔐 Аутентификация...")
            response = requests.post(auth_url, json=auth_data, timeout=30)
            
            if response.status_code != 200:
                self.stdout.write(f"❌ Ошибка аутентификации: {response.status_code}")
                return
                
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                self.stdout.write("❌ Access token не получен")
                return
                
            self.stdout.write("✅ Аутентификация успешна")
            
            # Тестируем различные endpoints
            base_url = settings.AUTH_CONFIG['EXTERNAL_API']['BASE_URL']
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Список возможных endpoints для групп
            possible_endpoints = [
                '/domain/user/groups',
                '/user/groups',
                '/groups',
                '/user/domain/groups',
                '/auth/domain/user/groups',
                '/auth/user/groups',
                '/auth/groups',
                '/api/v1/auth/domain/user/groups',
                '/api/v1/auth/user/groups',
                '/api/v1/auth/groups'
            ]
            
            self.stdout.write("\n🔍 Тестирование endpoints для получения групп:")
            self.stdout.write("-" * 50)
            
            for endpoint in possible_endpoints:
                full_url = f"{base_url}{endpoint}"
                self.stdout.write(f"\nТестируем: {endpoint}")
                
                try:
                    response = requests.get(full_url, headers=headers, timeout=10)
                    self.stdout.write(f"  Статус: {response.status_code}")
                    
                    if response.status_code == 200:
                        self.stdout.write("  ✅ УСПЕХ! Endpoint найден!")
                        try:
                            data = response.json()
                            self.stdout.write(f"  Ответ: {json.dumps(data, ensure_ascii=False, indent=4)}")
                        except:
                            self.stdout.write(f"  Ответ: {response.text}")
                        break
                    elif response.status_code == 404:
                        self.stdout.write("  ❌ Not Found")
                    elif response.status_code == 401:
                        self.stdout.write("  ❌ Unauthorized")
                    elif response.status_code == 403:
                        self.stdout.write("  ❌ Forbidden")
                    else:
                        self.stdout.write(f"  ⚠️  Статус: {response.status_code}")
                        
                except Exception as e:
                    self.stdout.write(f"  ❌ Ошибка: {e}")
            
            # Тестируем базовый endpoint для проверки доступности API
            self.stdout.write("\n🔍 Тестирование базового API:")
            self.stdout.write("-" * 30)
            
            try:
                response = requests.get(base_url, timeout=10)
                self.stdout.write(f"Базовый URL: {base_url}")
                self.stdout.write(f"Статус: {response.status_code}")
                if response.content:
                    self.stdout.write(f"Ответ: {response.text[:200]}...")
            except Exception as e:
                self.stdout.write(f"Ошибка базового API: {e}")
                
        except Exception as e:
            self.stdout.write(f"❌ Критическая ошибка: {e}")
            import traceback
            self.stdout.write(f"Traceback: {traceback.format_exc()}")
