from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json

class Command(BaseCommand):
    help = 'Тестирует формат токена и заголовки для API'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('password', type=str, help='Пароль')
        parser.add_argument('domain', type=str, help='Домен')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        domain = options['domain']
        
        self.stdout.write(f"Тестирование формата токена для {username}@{domain}")
        self.stdout.write("=" * 60)
        
        # Получаем токены
        auth_url = f"{settings.AUTH_CONFIG['EXTERNAL_API']['BASE_URL']}/login"
        auth_data = {
            'username': username,
            'password': password,
            'domain': domain
        }
        
        try:
            self.stdout.write(f"Отправка запроса на: {auth_url}")
            self.stdout.write(f"Данные: {json.dumps(auth_data, ensure_ascii=False)}")
            
            response = requests.post(auth_url, json=auth_data, timeout=30)
            
            self.stdout.write(f"Статус: {response.status_code}")
            self.stdout.write(f"Заголовки ответа: {dict(response.headers)}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    self.stdout.write(f"✅ Access token получен")
                    self.stdout.write(f"Длина токена: {len(access_token)}")
                    self.stdout.write(f"Первые 50 символов: {access_token[:50]}...")
                    self.stdout.write(f"Последние 50 символов: ...{access_token[-50:]}")
                    
                    # Проверяем формат JWT
                    token_parts = access_token.split('.')
                    self.stdout.write(f"Количество частей JWT: {len(token_parts)}")
                    
                    if len(token_parts) == 3:
                        self.stdout.write("✅ Токен имеет правильный JWT формат")
                        
                        # Тестируем заголовок Authorization
                        auth_header = f"Bearer {access_token}"
                        self.stdout.write(f"Заголовок Authorization: {auth_header[:100]}...")
                        
                        # Тестируем запрос групп
                        groups_url = f"{settings.AUTH_CONFIG['EXTERNAL_API']['BASE_URL']}/domain/user/groups"
                        headers = {
                            'Authorization': auth_header,
                            'Content-Type': 'application/json'
                        }
                        
                        self.stdout.write(f"\nТестирование запроса групп:")
                        self.stdout.write(f"URL: {groups_url}")
                        self.stdout.write(f"Заголовки: {headers}")
                        
                        groups_response = requests.get(groups_url, headers=headers, timeout=30)
                        self.stdout.write(f"Статус ответа групп: {groups_response.status_code}")
                        self.stdout.write(f"Заголовки ответа групп: {dict(groups_response.headers)}")
                        
                        if groups_response.content:
                            try:
                                groups_data = groups_response.json()
                                self.stdout.write(f"Ответ групп: {json.dumps(groups_data, ensure_ascii=False, indent=2)}")
                            except:
                                self.stdout.write(f"Текстовый ответ групп: {groups_response.text}")
                        else:
                            self.stdout.write("Ответ групп пустой")
                            
                    else:
                        self.stdout.write(f"❌ Токен не имеет правильный JWT формат")
                        
                else:
                    self.stdout.write("❌ Access token не найден в ответе")
                    self.stdout.write(f"Полный ответ: {json.dumps(token_data, ensure_ascii=False, indent=2)}")
            else:
                self.stdout.write(f"❌ Ошибка аутентификации: {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        self.stdout.write(f"Ошибка: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                    except:
                        self.stdout.write(f"Ошибка: {response.text}")
                        
        except Exception as e:
            self.stdout.write(f"❌ Ошибка: {e}")
            import traceback
            self.stdout.write(f"Traceback: {traceback.format_exc()}")
