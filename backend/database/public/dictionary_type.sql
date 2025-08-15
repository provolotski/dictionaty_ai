create table dictionary_type
(
    id   integer generated always as identity
        constraint dictionary_type_pk
            primary key,
    name varchar
);

alter table dictionary_type
    owner to admin_eisgs;

