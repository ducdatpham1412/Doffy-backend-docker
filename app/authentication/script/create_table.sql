CREATE TABLE doffy.authentication_user_request (
	id int NOT NULL auto_increment,
    user_id BIGINT,
	type int NOT NULL,
    created DATETIME NOT NULL,
    expired DATETIME,
    status int NOT NULL,
    PRIMARY KEY(id),
	FOREIGN KEY(user_id) REFERENCES doffy.authentication_user(id) ON DELETE CASCADE
);