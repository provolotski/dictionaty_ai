#!/usr/bin/env python3
"""
Скрипт для тестирования LDAP аутентификации с ldap3
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from auth.ldap_auth_ldap3 import LDAPAuthenticator, AuthService
from config import settings

async def test_ldap_connection():
    """Тестирование подключения к LDAP"""
    print("🔍 Тестирование подключения к LDAP...")
    
    try:
        auth = LDAPAuthenticator()
        print(f"✅ LDAP сервер: {auth.ldap_server}")
        print(f"✅ База поиска: {auth.base_dn}")
        print(f"✅ SSL: {auth.use_ssl}")
        print(f"✅ TLS: {auth.use_tls}")
        
        # Тестирование подключения
        conn = auth._get_ldap_connection()
        print("✅ Подключение к LDAP успешно установлено")
        conn.unbind()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к LDAP: {e}")
        return False

async def test_user_search():
    """Тестирование поиска пользователя"""
    print("\n🔍 Тестирование поиска пользователя...")
    
    try:
        auth = LDAPAuthenticator()
        
        # Тестовый пользователь (замените на реального)
        test_username = "test_user"  # Замените на реальное имя пользователя
        
        user_dn = auth._find_user_dn(test_username)
        if user_dn:
            print(f"✅ Пользователь найден: {user_dn}")
            
            # Получение информации о пользователе
            user_info = auth._get_user_info(user_dn)
            if user_info:
                print("✅ Информация о пользователе получена:")
                for key, value in user_info.items():
                    print(f"   {key}: {value}")
            
            # Получение групп пользователя
            groups = auth._get_user_groups(user_dn)
            print(f"✅ Группы пользователя: {groups}")
            
            return True
        else:
            print(f"⚠️  Пользователь {test_username} не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка поиска пользователя: {e}")
        return False

async def test_group_membership():
    """Тестирование проверки членства в группе"""
    print("\n🔍 Тестирование проверки членства в группе...")
    
    try:
        auth = LDAPAuthenticator()
        
        # Тестовый пользователь и группа
        test_username = "test_user"  # Замените на реальное имя пользователя
        test_group = auth.required_group
        
        user_dn = auth._find_user_dn(test_username)
        if user_dn:
            is_member = auth._is_user_in_group(user_dn, test_group)
            print(f"✅ Пользователь {test_username} в группе {test_group}: {is_member}")
            return True
        else:
            print(f"⚠️  Пользователь {test_username} не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки членства в группе: {e}")
        return False

async def test_authentication():
    """Тестирование полной аутентификации"""
    print("\n🔍 Тестирование полной аутентификации...")
    
    try:
        auth_service = AuthService()
        
        # Тестовые учетные данные (замените на реальные)
        test_username = "test_user"  # Замените на реальное имя пользователя
        test_password = "test_password"  # Замените на реальный пароль
        
        result = await auth_service.authenticate_and_create_tokens(test_username, test_password)
        
        if result:
            print("✅ Аутентификация успешна!")
            print(f"✅ Access token: {result['access_token'][:50]}...")
            print(f"✅ Refresh token: {result['refresh_token'][:50]}...")
            print(f"✅ Пользователь: {result['user']['username']}")
            print(f"✅ Отображаемое имя: {result['user']['display_name']}")
            print(f"✅ Email: {result['user']['email']}")
            print(f"✅ Группы: {result['user']['groups']}")
            return True
        else:
            print("❌ Аутентификация не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка аутентификации: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование LDAP аутентификации с ldap3")
    print("=" * 50)
    
    # Проверка настроек
    print("📋 Проверка настроек LDAP:")
    print(f"   Сервер: {settings.ldap_server}")
    print(f"   Домен: {settings.ldap_domain}")
    print(f"   База поиска: {settings.ldap_base_dn}")
    print(f"   Группа: {settings.ldap_required_group}")
    print()
    
    # Тесты
    tests = [
        ("Подключение к LDAP", test_ldap_connection),
        ("Поиск пользователя", test_user_search),
        ("Проверка членства в группе", test_group_membership),
        ("Полная аутентификация", test_authentication),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте настройки LDAP.")

if __name__ == "__main__":
    asyncio.run(main())
