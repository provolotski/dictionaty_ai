#!/usr/bin/env python3
"""
Тест реальной авторизации через auth_manager
"""

import os
import sys
import django

# Добавляем путь к проекту Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DictionaryFront.settings')
django.setup()

from accounts.auth_manager import auth_manager


def test_real_auth():
    """Тест реальной авторизации"""
    print("=== ТЕСТ РЕАЛЬНОЙ АВТОРИЗАЦИИ ===")
    
    # Тестовые учетные данные (замените на реальные)
    test_cases = [
        {
            'username': 'admin_db_app',
            'password': '47khTCzG',
            'domain': 'belstat'
        },
        {
            'username': 'test_user',
            'password': 'wrong_password',
            'domain': 'test_domain'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Тест {i} ---")
        print(f"Пользователь: {test_case['username']}")
        print(f"Домен: {test_case['domain']}")
        
        try:
            success, token_data, error_message = auth_manager.authenticate_user(
                test_case['username'],
                test_case['password'],
                test_case['domain']
            )
            
            print(f"Результат: {'✅ УСПЕХ' if success else '❌ ОШИБКА'}")
            
            if success:
                print(f"Токены получены: access={bool(token_data.get('access_token'))}, refresh={bool(token_data.get('refresh_token'))}")
                if token_data.get('user_info'):
                    user_info = token_data['user_info']
                    print(f"Информация о пользователе: ID={user_info.get('id')}, username={user_info.get('username')}")
            else:
                print(f"Сообщение об ошибке: {error_message}")
                
        except Exception as e:
            print(f"❌ Исключение: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")


if __name__ == '__main__':
    test_real_auth()
