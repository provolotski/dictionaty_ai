# Миграция с python-ldap на ldap3

## Обзор изменений

Заменена библиотека `python-ldap` на `ldap3` для улучшения совместимости с Python 3.12 и упрощения кода.

## Преимущества ldap3

1. **Лучшая совместимость** - полностью совместима с Python 3.12
2. **Простота использования** - более чистый и понятный API
3. **Автоматическое управление соединениями** - меньше ручного управления
4. **Лучшая обработка ошибок** - более информативные исключения
5. **Поддержка современных протоколов** - лучшее SSL/TLS

## Что было изменено

### 1. Зависимости

**Было:**
```
python-ldap==3.4.3
```

**Стало:**
```
ldap3==2.9.1
```

### 2. Основные изменения в коде

#### Импорты

**Было:**
```python
import ldap
```

**Стало:**
```python
from ldap3 import Server, Connection, ALL, SUBTREE, LEVEL, SIMPLE, ANONYMOUS
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPInvalidCredentialsError
```

#### Создание соединения

**Было:**
```python
conn = ldap.initialize(f"ldaps://{self.ldap_server}")
conn.simple_bind_s(user_dn, password)
```

**Стало:**
```python
server = Server(self.ldap_server, use_ssl=self.use_ssl, get_info=ALL)
conn = Connection(server, user=user_dn, password=password, 
                 authentication=SIMPLE, auto_bind=True)
```

#### Поиск в LDAP

**Было:**
```python
result = conn.search_s(
    self.user_search_base,
    ldap.SCOPE_SUBTREE,
    filter_str,
    attrs
)
```

**Стало:**
```python
conn.search(
    search_base=self.user_search_base,
    search_filter=filter_str,
    search_scope=SUBTREE,
    attributes=attrs
)
```

#### Обработка результатов

**Было:**
```python
if result and len(result) > 0:
    return result[0][0]  # DN
```

**Стало:**
```python
if conn.entries:
    return conn.entries[0].entry_dn
```

#### Обработка ошибок

**Было:**
```python
except ldap.INVALID_CREDENTIALS:
    # обработка ошибки
```

**Стало:**
```python
except LDAPInvalidCredentialsError:
    # обработка ошибки
```

## Файлы

### Новые файлы:
- `auth/ldap_auth_ldap3.py` - новая реализация с ldap3
- `test_ldap3_auth.py` - скрипт тестирования

### Измененные файлы:
- `auth/__init__.py` - обновлен импорт
- `requirements.txt` - заменена зависимость
- `requirements_py312.txt` - заменена зависимость

## Тестирование

Запустите тест новой аутентификации:

```bash
cd backend
python test_ldap3_auth.py
```

## Откат изменений

Если нужно вернуться к python-ldap:

1. Обновите `auth/__init__.py`:
```python
from .ldap_auth import (
    AuthService,
    get_current_user,
    require_group,
    auth_service
)
```

2. Обновите requirements:
```
python-ldap==3.4.3
```

3. Удалите новые файлы:
```bash
rm auth/ldap_auth_ldap3.py
rm test_ldap3_auth.py
```

## Совместимость

Новая реализация полностью совместима с существующим API:
- Все функции имеют те же сигнатуры
- Возвращаемые значения не изменились
- Обработка ошибок улучшена, но интерфейс тот же

## Рекомендации

1. **Тестирование** - обязательно протестируйте в тестовой среде
2. **Мониторинг** - следите за логами после развертывания
3. **Резервное копирование** - сохраните старую версию на случай отката
4. **Документация** - обновите документацию по аутентификации

## Известные различия

1. **Таймауты** - ldap3 использует `receive_timeout` вместо `OPT_NETWORK_TIMEOUT`
2. **SSL/TLS** - более простая настройка в ldap3
3. **Результаты поиска** - доступ через `conn.entries` вместо кортежей
4. **Кодировка** - ldap3 автоматически обрабатывает кодировку

## Поддержка

При возникновении проблем:
1. Проверьте логи аутентификации
2. Запустите тест: `python test_ldap3_auth.py`
3. Сравните настройки с документацией ldap3
4. При необходимости откатитесь к старой версии
