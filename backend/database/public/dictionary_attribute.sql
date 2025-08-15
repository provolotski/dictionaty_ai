create table dictionary_attribute
(
    id            integer generated always as identity
        constraint dictionary_attribute_pk
            primary key,
    id_dictionary integer
        constraint dictionary_attribute_dictionary_id_fk
            references dictionary,
    name          varchar,
    required      boolean,
    start_date    date,
    finish_date   date,
    capacity    integer,
    alt_name      varchar,
    id_attribute_type integer
);

alter table dictionary_attribute
    owner to admin_eisgs;

create unique index dictionary_attribute_id_dictionary_alt_name_uindex
    on dictionary_attribute (id_dictionary, alt_name);

