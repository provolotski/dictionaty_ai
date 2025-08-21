-- Добавление новых полей в таблицу users
-- Поле "подразделение" (department) и "is_user" (логическое поле)

-- Проверяем, существует ли таблица users
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION 'Таблица users не существует. Сначала создайте таблицу.';
    END IF;
END $$;

-- Добавляем поле department для хранения подразделения (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'department') THEN
        ALTER TABLE users ADD COLUMN department VARCHAR(255);
        RAISE NOTICE 'Добавлено поле department';
    ELSE
        RAISE NOTICE 'Поле department уже существует';
    END IF;
END $$;

-- Добавляем поле is_user для указания вхождения в группу EISGS_Users (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_user') THEN
        ALTER TABLE users ADD COLUMN is_user BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Добавлено поле is_user';
    ELSE
        RAISE NOTICE 'Поле is_user уже существует';
    END IF;
END $$;

-- Добавляем поле is_active для указания активности пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_active') THEN
        ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Добавлено поле is_active';
    ELSE
        RAISE NOTICE 'Поле is_active уже существует';
    END IF;
END $$;

-- Добавляем поле updated_at для отслеживания изменений (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'updated_at') THEN
        ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Добавлено поле updated_at';
    ELSE
        RAISE NOTICE 'Поле updated_at уже существует';
    END IF;
END $$;

-- Добавляем комментарии к новым полям
COMMENT ON COLUMN users.department IS 'Подразделение пользователя (из атрибута OU)';
COMMENT ON COLUMN users.is_user IS 'Флаг вхождения пользователя в группу EISGS_Users';
COMMENT ON COLUMN users.is_active IS 'Флаг активности пользователя';
COMMENT ON COLUMN users.updated_at IS 'Дата последнего обновления записи';

-- Создаем индексы для быстрого поиска (если не существуют)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_users_department') THEN
        CREATE INDEX idx_users_department ON users(department);
        RAISE NOTICE 'Создан индекс idx_users_department';
    ELSE
        RAISE NOTICE 'Индекс idx_users_department уже существует';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_users_is_user') THEN
        CREATE INDEX idx_users_is_user ON users(is_user);
        RAISE NOTICE 'Создан индекс idx_users_is_user';
    ELSE
        RAISE NOTICE 'Индекс idx_users_is_user уже существует';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_users_is_active') THEN
        CREATE INDEX idx_users_is_active ON users(is_active);
        RAISE NOTICE 'Создан индекс idx_users_is_active';
    ELSE
        RAISE NOTICE 'Индекс idx_users_is_active уже существует';
    END IF;
END $$;

-- Создаем триггер для автоматического обновления updated_at (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        RAISE NOTICE 'Создана функция update_updated_at_column';
    ELSE
        RAISE NOTICE 'Функция update_updated_at_column уже существует';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'update_users_updated_at') THEN
        CREATE TRIGGER update_users_updated_at 
            BEFORE UPDATE ON users 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Создан триггер update_users_updated_at';
    ELSE
        RAISE NOTICE 'Триггер update_users_updated_at уже существует';
    END IF;
END $$;

-- Обновляем существующие записи, устанавливая значения по умолчанию
UPDATE users SET 
    is_active = COALESCE(is_active, TRUE),
    is_user = COALESCE(is_user, FALSE),
    updated_at = CURRENT_TIMESTAMP
WHERE is_active IS NULL OR is_user IS NULL OR updated_at IS NULL;

-- Проверяем структуру таблицы
\d users;
