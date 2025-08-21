-- Создание таблицы users с правильной структурой
-- Включает все необходимые поля для расширенной функциональности

-- Сначала удаляем существующую таблицу (если есть)
DROP TABLE IF EXISTS users CASCADE;

-- Создаем таблицу users с новой структурой
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    guid VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    department VARCHAR(255),
    is_user BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для оптимизации запросов
CREATE INDEX idx_users_guid ON users(guid);
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_is_user ON users(is_user);
CREATE INDEX idx_users_is_admin ON users(is_admin);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Добавляем комментарии к таблице и колонкам
COMMENT ON TABLE users IS 'Таблица пользователей системы';
COMMENT ON COLUMN users.id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN users.guid IS 'GUID пользователя из Active Directory';
COMMENT ON COLUMN users.name IS 'Имя пользователя';
COMMENT ON COLUMN users.is_active IS 'Флаг активности пользователя';
COMMENT ON COLUMN users.is_admin IS 'Флаг администратора системы';
COMMENT ON COLUMN users.department IS 'Подразделение пользователя';
COMMENT ON COLUMN users.is_user IS 'Флаг вхождения в группу EISGS_Users';
COMMENT ON COLUMN users.created_at IS 'Дата создания записи';
COMMENT ON COLUMN users.updated_at IS 'Дата последнего обновления';

-- Устанавливаем владельца таблицы
ALTER TABLE users OWNER TO admin_eisgs;

-- Создаем триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Вставляем тестовые данные (опционально)
INSERT INTO users (guid, name, is_active, is_admin, department, is_user) VALUES
('{test-guid-1}', 'Тестовый Администратор', TRUE, TRUE, 'IT', TRUE),
('{test-guid-2}', 'Тестовый Пользователь', TRUE, FALSE, 'HR', TRUE),
('{test-guid-3}', 'Тестовый Владелец', TRUE, FALSE, 'Finance', TRUE);

-- Проверяем структуру таблицы
\d users;