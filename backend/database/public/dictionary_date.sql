create table dictionary_date
(
    id           integer generated always as identity
        constraint dictionary_date_pk
            primary key,
    id_position  integer
        constraint dictionary_date_dictionary_positions_id_fk
            references dictionary_positions,
    id_attribute integer
        constraint dictionary_date_dictionary_attribute_id_fk
            references dictionary_attribute,
    value        varchar,
    start_date   date,
    finish_date  date
);

alter table dictionary_date
    owner to admin_eisgs;

