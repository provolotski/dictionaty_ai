create table dictionary_owner
(
    id            integer generated always as identity
        constraint dictionary_owner_pk
            primary key,
    id_dictionary integer
        constraint dictionary_owner_dictionary_id_fk
            references dictionary,
    id_user      integer
        constraint dictionary_owner_user_id_fk
            references users,
    created_at   timestamp default current_timestamp,
    updated_at   timestamp default current_timestamp
);

-- Создаем уникальный индекс для предотвращения дублирования
create unique index dictionary_owner_dictionary_user_uindex
    on dictionary_owner (id_dictionary, id_user);

-- Добавляем комментарии к таблице и колонкам
comment on table dictionary_owner is 'Таблица для определения владельцев справочников';
comment on column dictionary_owner.id is 'Уникальный идентификатор записи';
comment on column dictionary_owner.id_dictionary is 'Идентификатор справочника';
comment on column dictionary_owner.id_user is 'Идентификатор пользователя-владельца';
comment on column dictionary_owner.created_at is 'Дата создания записи';
comment on column dictionary_owner.updated_at is 'Дата последнего обновления записи';

-- Устанавливаем владельца таблицы
alter table dictionary_owner
    owner to admin_eisgs;
