CREATE TABLE public.estado_archivos (
	id serial4 NOT NULL,
	nombre_archivo varchar NOT NULL,
	nuevo_archivo varchar NOT NULL,
	estado varchar NOT NULL,
	extension_original varchar NULL,
	extension_nueva varchar NULL,
	fecha_carga timestamp NULL,
	usuario_id integer NOT NULL,
	fecha_procesamiento timestamp NULL,
	CONSTRAINT estado_archivos_pk PRIMARY KEY (id)
);

CREATE TABLE public.users (
    id bigserial NOT NULL,
    username varchar NOT NULL,
    email varchar NOT NULL,
    password varchar NOT NULL,
    CONSTRAINT users_pk PRIMARY KEY (id),
	CONSTRAINT users_user_un UNIQUE (username),
	CONSTRAINT users_email_un UNIQUE (email)
);

ALTER TABLE public.estado_archivos
ADD CONSTRAINT fk_users
FOREIGN KEY (usuario_id)
REFERENCES public.users(id);