-- Миграция для добавления полей created_at и updated_at в таблицу dictionary
-- Выполнить: psql -d your_database -f add_timestamps_to_dictionary.sql

-- Добавляем поля created_at и updated_at
ALTER TABLE dictionary 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Обновляем существующие записи, устанавливая created_at и updated_at равными change_date
-- Если change_date NULL, используем текущую дату
UPDATE dictionary 
SET 
    created_at = COALESCE(change_date::timestamp, CURRENT_TIMESTAMP),
    updated_at = COALESCE(change_date::timestamp, CURRENT_TIMESTAMP)
WHERE created_at IS NULL OR updated_at IS NULL;

-- Создаем триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_dictionary_updated_at 
    BEFORE UPDATE ON dictionary 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
