create table dictionary_status
(
    id   integer generated always as identity
        constraint dictionary_status_pk
            primary key,
    name varchar
);

alter table dictionary_status
    owner to admin_eisgs;

