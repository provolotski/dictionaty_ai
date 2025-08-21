#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API endpoints владельцев справочников
"""

import requests
import json

# Настройки
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_api_endpoints():
    """Тестирование API endpoints"""
    
    print("=== Тестирование API endpoints владельцев справочников ===\n")
    
    # 1. Тест получения доступных справочников
    print("1. Тест получения доступных справочников")
    print(f"URL: {API_BASE}/users/dictionaries/available")
    
    try:
        response = requests.get(f"{API_BASE}/users/dictionaries/available", timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Количество справочников: {len(data)}")
        else:
            print("❌ Ошибка получения справочников")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Тест получения пользователя с владением (ID = 1)
    print("2. Тест получения пользователя с владением (ID = 1)")
    print(f"URL: {API_BASE}/users/1/with-ownership")
    
    try:
        response = requests.get(f"{API_BASE}/users/1/with-ownership", timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Пользователь получен успешно")
        elif response.status_code == 404:
            print("ℹ️ Пользователь с ID = 1 не найден")
        else:
            print("❌ Ошибка получения пользователя")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. Тест получения списка пользователей
    print("3. Тест получения списка пользователей")
    print(f"URL: {API_BASE}/users/")
    
    try:
        response = requests.get(f"{API_BASE}/users/", timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Количество пользователей: {data.get('total', 0)}")
            if data.get('users'):
                print(f"Первый пользователь: {data['users'][0].get('name', 'N/A')}")
        else:
            print("❌ Ошибка получения списка пользователей")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 4. Проверка доступности backend сервера
    print("4. Проверка доступности backend сервера")
    print(f"URL: {BASE_URL}/health")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend сервер доступен")
        else:
            print("⚠️ Backend сервер отвечает, но статус не 200")
    except Exception as e:
        print(f"❌ Backend сервер недоступен: {e}")

if __name__ == "__main__":
    test_api_endpoints()
