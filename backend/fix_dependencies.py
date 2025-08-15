#!/usr/bin/env python3
"""
Скрипт для исправления проблем с зависимостями
Решает проблемы совместимости с Python 3.12
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n{description}...")
    print(f"Выполняется: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print("✅ Успешно выполнено")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Основная функция исправления зависимостей"""
    print("🔧 Исправление проблем с зависимостями для Python 3.12")
    
    # Проверяем версию Python
    python_version = sys.version_info
    print(f"Python версия: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 12:
        print("⚠️  Этот скрипт предназначен для Python 3.12+")
        return
    
    # Переходим в директорию backend
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    print(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Удаляем существующее виртуальное окружение
    if Path("venv").exists():
        print("\n🗑️  Удаление старого виртуального окружения...")
        run_command("rm -rf venv", "Удаление venv")
    
    # Создаем новое виртуальное окружение
    run_command("python3 -m venv venv", "Создание нового виртуального окружения")
    
    # Активируем виртуальное окружение
    activate_script = "venv/bin/activate"
    if not os.path.exists(activate_script):
        activate_script = "venv\\Scripts\\activate"  # Для Windows
    
    # Обновляем pip
    run_command("venv/bin/pip install --upgrade pip", "Обновление pip")
    
    # Устанавливаем wheel и setuptools
    run_command("venv/bin/pip install --upgrade wheel setuptools", 
                "Установка wheel и setuptools")
    
    # Устанавливаем numpy отдельно (новая версия)
    print("\n📦 Установка numpy (совместимая версия)...")
    run_command("venv/bin/pip install 'numpy>=1.26.0'", "Установка numpy")
    
    # Устанавливаем pandas отдельно
    print("\n📦 Установка pandas (совместимая версия)...")
    run_command("venv/bin/pip install 'pandas>=2.2.0'", "Установка pandas")
    
    # Устанавливаем остальные зависимости
    print("\n📦 Установка остальных зависимостей...")
    success = run_command("venv/bin/pip install -r requirements_py312.txt", 
                         "Установка зависимостей")
    
    if success:
        print("\n✅ Все зависимости успешно установлены!")
        print("\nДля активации виртуального окружения выполните:")
        print("source venv/bin/activate")
    else:
        print("\n❌ Возникли проблемы при установке зависимостей")
        print("Попробуйте установить зависимости вручную:")
        print("source venv/bin/activate")
        print("pip install -r requirements_py312.txt")

if __name__ == "__main__":
    main()
