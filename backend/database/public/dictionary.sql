create table dictionary
(
    id              serial
        constraint dictionary_pk
            primary key,
    name            varchar,
    code            varchar,
    description     varchar,
    start_date      date,
    finish_date     date,
    change_date     date,
    name_eng        varchar,
    name_bel        varchar,
    description_eng varchar,
    description_bel varchar,
    gko             varchar,
    organization    varchar,
    classifier      varchar,
    id_status       integer
        constraint dictionary_dictionary_status_id_fk
            references dictionary_status,
    id_type         integer
        constraint dictionary_dictionary_type_id_fk
            references dictionary_type,
    created_at      timestamp default current_timestamp,
    updated_at      timestamp default current_timestamp
);

alter table dictionary
    owner to admin_eisgs;

