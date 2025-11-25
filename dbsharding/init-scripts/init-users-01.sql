create user if not exists 'testuser'@'%' identified by 'testpass';
grant all privileges on userdb.* to 'testuser'@'%';
flush privileges;
