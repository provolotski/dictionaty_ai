// Основной класс для управления формой логина
class LoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.usernameInput = this.form.querySelector('input[name="username"]');
        this.passwordInput = this.form.querySelector('input[name="password"]');
        this.domainInput = this.form.querySelector('input[name="domain"]');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.loginButton = document.getElementById('loginButton');
        this.rememberMeCheckbox = document.getElementById('rememberMe');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSavedCredentials();
        this.setupAnimations();
    }
    
    setupEventListeners() {
        // Обработка показа/скрытия пароля
        this.passwordToggle.addEventListener('click', () => {
            this.togglePasswordVisibility();
        });
        
        // Обработка отправки формы
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Анимации при фокусе на полях
        this.usernameInput.addEventListener('focus', () => {
            this.animateInputFocus(this.usernameInput.parentElement);
        });
        
        this.passwordInput.addEventListener('focus', () => {
            this.animateInputFocus(this.passwordInput.parentElement);
        });
        
        this.domainInput.addEventListener('focus', () => {
            this.animateInputFocus(this.domainInput.parentElement);
        });
        
        // Валидация в реальном времени
        this.usernameInput.addEventListener('input', () => {
            this.validateUsername();
        });
        
        this.passwordInput.addEventListener('input', () => {
            this.validatePassword();
        });
        
        // Сохранение учетных данных при изменении чекбокса
        this.rememberMeCheckbox.addEventListener('change', () => {
            this.handleRememberMeChange();
        });
        
        // Обработка клавиши Enter
        this.form.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSubmit();
            }
        });
    }
    
    togglePasswordVisibility() {
        const type = this.passwordInput.type === 'password' ? 'text' : 'password';
        this.passwordInput.type = type;
        
        const icon = this.passwordToggle.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
        
        // Анимация иконки
        this.passwordToggle.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.passwordToggle.style.transform = 'scale(1)';
        }, 100);
    }
    
    animateInputFocus(inputContainer) {
        // Добавляем класс для анимации
        inputContainer.classList.add('focused');
        
        // Убираем класс через некоторое время
        setTimeout(() => {
            inputContainer.classList.remove('focused');
        }, 300);
    }
    
    validateUsername() {
        const username = this.usernameInput.value.trim();
        const container = this.usernameInput.parentElement;
        
        if (username.length === 0) {
            this.showInputError(container, 'Имя пользователя обязательно');
            return false;
        } else if (username.length < 3) {
            this.showInputError(container, 'Имя пользователя должно содержать минимум 3 символа');
            return false;
        } else {
            this.clearInputError(container);
            return true;
        }
    }
    
    validatePassword() {
        const password = this.passwordInput.value;
        const container = this.passwordInput.parentElement;
        
        if (password.length === 0) {
            this.showInputError(container, 'Пароль обязателен');
            return false;
        } else if (password.length < 6) {
            this.showInputError(container, 'Пароль должен содержать минимум 6 символов');
            return false;
        } else {
            this.clearInputError(container);
            return true;
        }
    }
    
    showInputError(container, message) {
        // Удаляем существующую ошибку
        this.clearInputError(container);
        
        // Создаем элемент ошибки
        const errorElement = document.createElement('div');
        errorElement.className = 'input-error';
        errorElement.textContent = message;
        
        // Добавляем стили
        errorElement.style.cssText = `
            color: #c53030;
            font-size: 0.8rem;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: #fee;
            border-radius: 6px;
            border: 1px solid #fed7d7;
            animation: slideIn 0.3s ease-out;
        `;
        
        container.appendChild(errorElement);
        container.style.borderColor = '#c53030';
    }
    
    clearInputError(container) {
        const existingError = container.querySelector('.input-error');
        if (existingError) {
            existingError.remove();
        }
        container.style.borderColor = '';
    }
    
    async handleSubmit() {
        // Валидация
        const isUsernameValid = this.validateUsername();
        const isPasswordValid = this.validatePassword();
        
        if (!isUsernameValid || !isPasswordValid) {
            this.showFormError('Пожалуйста, исправьте ошибки в форме');
            return;
        }
        
        // Показываем состояние загрузки
        this.setLoadingState(true);
        
        try {
            // Создаем FormData
            const formData = new FormData(this.form);
            
            // Отправляем запрос
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.handleSuccess(result);
            } else {
                this.handleError(result.error || 'Ошибка аутентификации');
            }
            
        } catch (error) {
            console.error('Ошибка при отправке формы:', error);
            this.handleError('Ошибка сети. Проверьте подключение к интернету.');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    setLoadingState(loading) {
        if (loading) {
            this.loginButton.classList.add('loading');
            this.loginButton.disabled = true;
        } else {
            this.loginButton.classList.remove('loading');
            this.loginButton.disabled = false;
        }
    }
    
    handleSuccess(result) {
        // Сохраняем учетные данные если выбрано "Запомнить меня"
        if (this.rememberMeCheckbox.checked) {
            this.saveCredentials();
        } else {
            this.clearSavedCredentials();
        }
        
        // Показываем сообщение об успехе
        this.showFormSuccess('Вход выполнен успешно! Перенаправление...');
        
        // Перенаправляем через 1 секунду
        setTimeout(() => {
            window.location.href = result.redirect_url || '/dashboard';
        }, 1000);
    }
    
    handleError(message) {
        this.showFormError(message);
    }
    
    showFormError(message) {
        this.showMessage('error', message);
    }
    
    showFormSuccess(message) {
        this.showMessage('success', message);
    }
    
    showMessage(type, message) {
        // Удаляем существующие сообщения
        const existingMessages = document.querySelectorAll('.error-message, .success-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Создаем новое сообщение
        const messageElement = document.createElement('div');
        messageElement.className = `${type}-message`;
        messageElement.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Добавляем стили
        messageElement.style.cssText = `
            display: flex;
            align-items: center;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 0.9rem;
            animation: slideIn 0.3s ease-out;
            ${type === 'error' ? 
                'background: #fee; color: #c53030; border: 1px solid #fed7d7;' : 
                'background: #f0fff4; color: #38a169; border: 1px solid #c6f6d5;'
            }
        `;
        
        // Вставляем после кнопки
        this.loginButton.parentNode.insertBefore(messageElement, this.loginButton.nextSibling);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => {
                    if (messageElement.parentNode) {
                        messageElement.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    saveCredentials() {
        const credentials = {
            username: this.usernameInput.value,
            remember: true
        };
        localStorage.setItem('loginCredentials', JSON.stringify(credentials));
    }
    
    clearSavedCredentials() {
        localStorage.removeItem('loginCredentials');
    }
    
    loadSavedCredentials() {
        try {
            const saved = localStorage.getItem('loginCredentials');
            if (saved) {
                const credentials = JSON.parse(saved);
                if (credentials.remember && credentials.username) {
                    this.usernameInput.value = credentials.username;
                    this.rememberMeCheckbox.checked = true;
                }
            }
        } catch (error) {
            console.error('Ошибка при загрузке сохраненных учетных данных:', error);
        }
    }
    
    handleRememberMeChange() {
        if (!this.rememberMeCheckbox.checked) {
            this.clearSavedCredentials();
        }
    }
    
    setupAnimations() {
        // Добавляем CSS анимации
        const style = document.createElement('style');
        style.textContent = `
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
            
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px);
                }
            }
            
            .input-container.focused {
                transform: scale(1.02);
            }
            
            .input-container {
                transition: transform 0.2s ease;
            }
        `;
        document.head.appendChild(style);
    }
    
    getCSRFToken() {
        // Получаем CSRF токен из cookie или из скрытого поля
        const csrfCookie = document.cookie.split(';').find(cookie => 
            cookie.trim().startsWith('csrftoken=')
        );
        
        if (csrfCookie) {
            return csrfCookie.split('=')[1];
        }
        
        // Если нет в cookie, ищем в скрытом поле
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
}

// Утилиты для работы с формами
class FormUtils {
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    static sanitizeInput(input) {
        return input.replace(/[<>]/g, '');
    }
}

// Анимации для фоновых элементов
class BackgroundAnimations {
    constructor() {
        this.shapes = document.querySelectorAll('.floating-shape');
        this.init();
    }
    
    init() {
        this.shapes.forEach((shape, index) => {
            this.animateShape(shape, index);
        });
    }
    
    animateShape(shape, index) {
        const duration = 6000 + (index * 1000);
        const delay = index * 500;
        
        shape.style.animation = `float ${duration}ms ease-in-out ${delay}ms infinite`;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем форму логина
    const loginForm = new LoginForm();
    
    // Инициализируем фоновые анимации
    const backgroundAnimations = new BackgroundAnimations();
    
    // Добавляем глобальные обработчики
    setupGlobalHandlers();
});

function setupGlobalHandlers() {
    // Обработка нажатия Escape для закрытия сообщений
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const messages = document.querySelectorAll('.error-message, .success-message');
            messages.forEach(msg => {
                msg.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => msg.remove(), 300);
            });
        }
    });
    
    // Обработка клика вне формы для снятия фокуса
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.login-form-container')) {
            const focusedInputs = document.querySelectorAll('.input-container:focus-within');
            focusedInputs.forEach(container => {
                container.classList.remove('focused');
            });
        }
    });
}

// Экспорт для использования в других модулях
window.LoginForm = LoginForm;
window.FormUtils = FormUtils;
window.BackgroundAnimations = BackgroundAnimations;
