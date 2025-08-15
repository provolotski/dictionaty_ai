create table dictionary_positions
(
    id            integer generated always as identity
        constraint dictionary_positions_pk
            primary key,
    id_dictionary integer
        constraint dictionary_positions_dictionary_id_fk
            references dictionary
);

alter table dictionary_positions
    owner to admin_eisgs;

