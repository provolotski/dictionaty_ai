# Форма логина с полем домена

## 📋 Обзор изменений

Форма логина была обновлена для работы с внешним API аутентификации, который требует поле `domain` в запросе.

### 🔄 Изменения в коде

#### 1. Django Form (`frontend/accounts/forms.py`)
```python
class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя пользователя',
            'autocomplete': 'username'
        }),
        label='Имя пользователя'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль',
            'autocomplete': 'current-password'
        }),
        label='Пароль'
    )
    domain = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Домен',
            'autocomplete': 'off'
        }),
        label='Домен',
        initial='default'
    )
```

#### 2. View (`frontend/accounts/views.py`)
```python
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            domain = form.cleaned_data['domain']
            
            login_data = {
                'username': username,
                'password': password,
                'domain': domain
            }
            # ... остальная логика
```

#### 3. Шаблон (`frontend/templates/login.html`)
```html
<!-- Поле имени пользователя -->
<div class="form-group">
    <div class="input-container">
        <div class="input-icon">
            <i class="fas fa-user"></i>
        </div>
        {{ form.username }}
        <div class="input-focus-border"></div>
    </div>
    {% if form.username.errors %}
    <div class="field-error">
        {% for error in form.username.errors %}
            <span>{{ error }}</span>
        {% endfor %}
    </div>
    {% endif %}
</div>

<!-- Поле пароля -->
<div class="form-group">
    <div class="input-container">
        <div class="input-icon">
            <i class="fas fa-lock"></i>
        </div>
        {{ form.password }}
        <button type="button" class="password-toggle" id="passwordToggle">
            <i class="fas fa-eye"></i>
        </button>
        <div class="input-focus-border"></div>
    </div>
    {% if form.password.errors %}
    <div class="field-error">
        {% for error in form.password.errors %}
            <span>{{ error }}</span>
        {% endfor %}
    </div>
    {% endif %}
</div>

<!-- Поле домена -->
<div class="form-group">
    <div class="input-container">
        <div class="input-icon">
            <i class="fas fa-globe"></i>
        </div>
        {{ form.domain }}
        <div class="input-focus-border"></div>
    </div>
    {% if form.domain.errors %}
    <div class="field-error">
        {% for error in form.domain.errors %}
            <span>{{ error }}</span>
        {% endfor %}
    </div>
    {% endif %}
</div>
```

## 📤 Формат данных для API

### Запрос
```json
{
    "username": "string",
    "password": "string", 
    "domain": "string"
}
```

### Примеры доменов
- `"default"` - стандартный домен
- `"belstat.local"` - локальный домен
- `"corp.example.com"` - корпоративный домен

### Ответ API
```json
{
    "access_token": "jwt_access_token_here",
    "refresh_token": "jwt_refresh_token_here"
}
```

## 🎨 Стили

### Ошибки полей
```css
.field-error {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    font-size: 0.75rem;
    color: #ef4444;
    animation: slideIn 0.3s ease;
}
```

### Анимация
```css
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

## 🧪 Тестирование

### 1. Тест API
```bash
cd frontend
python3 test_form_with_domain.py
```

### 2. Тест в браузере
- Откройте: `http://localhost:8001/accounts/login/`
- Проверьте наличие поля домена
- Убедитесь, что значение по умолчанию: `default`
- Протестируйте валидацию

### 3. Тест с реальными данными
```bash
python3 test_real_auth.py
```

## ✅ Функциональность

### Валидация
- ✅ Проверка обязательных полей
- ✅ Валидация длины имени пользователя (мин. 3 символа)
- ✅ Валидация пароля (мин. 6 символов)
- ✅ Отображение ошибок валидации

### UI/UX
- ✅ Красивое поле домена с иконкой глобуса
- ✅ Анимации при фокусе
- ✅ Сохранение введенных данных при ошибке
- ✅ Адаптивный дизайн

### Безопасность
- ✅ CSRF защита
- ✅ Валидация на сервере
- ✅ Безопасная передача данных

## 🔧 Настройка

### Изменение домена по умолчанию
Отредактируйте `frontend/accounts/forms.py`:
```python
domain = forms.CharField(
    # ...
    initial='your_default_domain'  # Измените здесь
)
```

### Добавление валидации домена
```python
def clean_domain(self):
    domain = self.cleaned_data['domain']
    if not domain:
        raise forms.ValidationError('Домен обязателен')
    return domain.strip()
```

## 🚨 Устранение неполадок

### Проблема: Поле домена не отображается
**Решение:**
1. Проверьте, что форма передается в контекст шаблона
2. Убедитесь, что `{{ form.domain }}` присутствует в шаблоне

### Проблема: Ошибка валидации домена
**Решение:**
1. Проверьте, что домен не пустой
2. Убедитесь, что домен соответствует требованиям API

### Проблема: API не принимает домен
**Решение:**
1. Проверьте формат данных в запросе
2. Убедитесь, что все поля присутствуют
3. Проверьте логи API

## 📊 Мониторинг

### Логи для отслеживания
```bash
# Просмотр логов формы
tail -f frontend/logs/belstat.log | grep "login"

# Поиск ошибок домена
grep "domain" frontend/logs/belstat.log
```

### Метрики
- Количество попыток входа с разными доменами
- Частота ошибок валидации домена
- Время ответа API для разных доменов

## 🔄 Совместимость

### Браузеры
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Устройства
- ✅ Десктоп
- ✅ Планшет
- ✅ Мобильный

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `frontend/logs/`
2. Запустите тестовые скрипты
3. Проверьте доступность API
4. Обратитесь к администратору системы




