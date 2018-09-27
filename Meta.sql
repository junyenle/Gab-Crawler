DROP DATABASE Meta;

CREATE DATABASE IF NOT EXISTS `Meta` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
USE `Meta`;


-- CREATE TABLE "Bots" -----------------------------------
CREATE TABLE `Bots` ( 
	`name` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL);
-- -------------------------------------------------------