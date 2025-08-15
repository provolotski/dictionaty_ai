create table attribute_type
(
    id   integer generated always as identity
        constraint attribute_type_pk
            primary key,
    name varchar
);

alter table attribute_type
    owner to admin_eisgs;

