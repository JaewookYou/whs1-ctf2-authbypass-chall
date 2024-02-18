SET collation_connection = 'utf8_general_ci';

#drop database chall;
create database chall;
ALTER DATABASE chall CHARACTER SET utf8 COLLATE utf8_general_ci;

use chall;

#drop table users;

create user 'user'@'%' identified by 'asdfasdf';

create table users(
	userseq int not null auto_increment primary key,
	userid varchar(50) not null, 
	userpw varchar(255) not null,
	phonenum char(13) not null,
	acctno char(36) not null,
	balance bigint not null default 10000,
	simplepass varchar(255),
	simplepass_key varchar(255),
	INDEX `index_acctno` (`acctno`)
) auto_increment=100000;

CREATE TABLE transactions (
    transaction_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    from_address VARCHAR(255),
    to_address VARCHAR(255),
    amount bigint NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE users CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;

grant all privileges on chall.* to 'user'@'%';

flush privileges;