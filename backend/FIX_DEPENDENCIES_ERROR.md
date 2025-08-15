# Исправление ошибок зависимостей для Python 3.12

## Проблема
Ошибка при установке numpy 1.25.2:
```
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'. Did you mean: 'zipimporter'?
```

## Причина
Numpy 1.25.2 не совместим с Python 3.12. В Python 3.12 был удален `pkgutil.ImpImporter`, который использовался в старых версиях numpy.

## Решение

### Вариант 1: Автоматическое исправление (рекомендуется)

Запустите скрипт исправления:
```bash
cd backend
python3 fix_dependencies.py
```

### Вариант 2: Ручное исправление

1. **Удалите старое виртуальное окружение:**
   ```bash
   cd backend
   rm -rf venv
   ```

2. **Создайте новое виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Обновите pip и установите базовые пакеты:**
   ```bash
   pip install --upgrade pip wheel setuptools
   ```

4. **Установите совместимые версии numpy и pandas:**
   ```bash
   pip install 'numpy>=1.26.0'
   pip install 'pandas>=2.2.0'
   ```

5. **Установите остальные зависимости:**
   ```bash
   pip install -r requirements_py312.txt
   ```

### Вариант 3: Использование conda (альтернатива)

Если у вас установлен conda:
```bash
cd backend
conda create -n dictionary_ai python=3.12
conda activate dictionary_ai
conda install numpy pandas
pip install -r requirements_py312.txt
```

## Что было изменено

1. **requirements.txt** - обновлены версии numpy и pandas
2. **requirements_py312.txt** - создан новый файл с гибкими версиями
3. **fix_dependencies.py** - скрипт автоматического исправления

## Совместимые версии для Python 3.12

- **numpy**: >= 1.26.0
- **pandas**: >= 2.2.0
- **fastapi**: >= 0.104.1
- **pydantic**: >= 2.5.0

## Проверка исправления

После установки зависимостей проверьте:
```bash
source venv/bin/activate
python -c "import numpy; print(f'numpy version: {numpy.__version__}')"
python -c "import pandas; print(f'pandas version: {pandas.__version__}')"
```

## Примечания

- Python 3.12 требует более новые версии многих пакетов
- Рекомендуется использовать виртуальные окружения
- При возникновении проблем с конкретными пакетами, попробуйте установить их отдельно

## Альтернативные решения

Если проблемы продолжаются:

1. **Используйте Python 3.11** (более стабильная версия)
2. **Используйте Docker** с предустановленными зависимостями
3. **Используйте conda** вместо pip для научных пакетов
