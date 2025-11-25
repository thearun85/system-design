create table if not exists users (
	user_id bigint not null primary key,
	username varchar(100) not null,
	email varchar(255) not null,
	created_at timestamp default current_timestamp,
	index idx_username (username),
	index idx_email (email)
) ENGINE = InnoDB;
