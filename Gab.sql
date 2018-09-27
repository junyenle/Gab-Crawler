-- Valentina Studio --
-- MySQL dump --
-- ---------------------------------------------------------
DROP DATABASE Gab;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
-- ---------------------------------------------------------


-- CREATE DATABASE "Gab" -----------------------------------
CREATE DATABASE IF NOT EXISTS `Gab` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
USE `Gab`;
-- ---------------------------------------------------------

-- CREATE TABLE "Follows" ----------------------------------
-- CREATE TABLE "Follows" --------------------------------------
CREATE TABLE `Follows` ( 
	`Follower` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
	`Followee` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB;
-- -------------------------------------------------------------
-- ---------------------------------------------------------

-- CREATE TABLE SEEN
CREATE TABLE `Seen` (`Username` VarChar (255)) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin;


-- CREATE TABLE "Hashtag" ----------------------------------
-- CREATE TABLE "Hashtag" --------------------------------------
CREATE TABLE `Hashtag` ( 
	`postId` Int( 255 ) NOT NULL,
	`hashtag` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE TABLE "Media" ------------------------------------
-- CREATE TABLE "Media" ----------------------------------------
CREATE TABLE `Media` ( 
	`url` VarChar( 400 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
	`postId` Int( 255 ) NOT NULL )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB;
-- -------------------------------------------------------------
-- ---------------------------------------------------------

-- CREATE TABLE "Links" ------------------------------------
-- CREATE TABLE "Links" ----------------------------------------
CREATE TABLE `Links` ( 
	`url` VarChar( 400 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    `text` Text,
	`postId` Int( 255 ) NOT NULL )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE TABLE "Post" -------------------------------------
-- CREATE TABLE "Post" -----------------------------------------
CREATE TABLE `Post` ( 
	`user` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
	`text` VarChar( 500 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
	`postId` Int( 255 ) AUTO_INCREMENT NOT NULL,
	`likes` Int( 255 ) NULL,
	`comments` Int( 255 ) NULL,
	`reposts` Int( 255 ) NULL,
	`date` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
	PRIMARY KEY ( `postId` ),
	CONSTRAINT `index1` UNIQUE( `postId` ) )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB
AUTO_INCREMENT = 128390;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE TABLE "User" -------------------------------------
-- CREATE TABLE "User" -----------------------------------------
CREATE TABLE `User` ( 
	`name` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
	`username` VarChar( 255 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
	`bio` VarChar( 500 ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL,
	`followers` Int( 255 ) NULL,
	`followings` Int( 255 ) NULL,
	CONSTRAINT `username` UNIQUE( `username` ) )
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_bin
ENGINE = InnoDB;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE INDEX "lnk_User_Follows" -------------------------
-- CREATE INDEX "lnk_User_Follows" -----------------------------
CREATE INDEX `lnk_User_Follows` USING BTREE ON `Follows`( `Followee` );
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE INDEX "lnk_User_Follows_2" -----------------------
-- CREATE INDEX "lnk_User_Follows_2" ---------------------------
CREATE INDEX `lnk_User_Follows_2` USING BTREE ON `Follows`( `Follower` );
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE INDEX "lnk_Post_Hashtag" -------------------------
-- CREATE INDEX "lnk_Post_Hashtag" -----------------------------
CREATE INDEX `lnk_Post_Hashtag` USING BTREE ON `Hashtag`( `postId` );
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE INDEX "lnk_Post_Media" ---------------------------
-- CREATE INDEX "lnk_Post_Media" -------------------------------
CREATE INDEX `lnk_Post_Media` USING BTREE ON `Media`( `postId` );
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE INDEX "lnk_User_Post" ----------------------------
-- CREATE INDEX "lnk_User_Post" --------------------------------
CREATE INDEX `lnk_User_Post` USING BTREE ON `Post`( `user` );
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE LINK "lnk_User_Follows" --------------------------
-- CREATE LINK "lnk_User_Follows" ------------------------------
ALTER TABLE `Follows`
	ADD CONSTRAINT `lnk_User_Follows` FOREIGN KEY ( `Followee` )
	REFERENCES `User`( `username` )
	ON DELETE Cascade
	ON UPDATE Cascade;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE LINK "lnk_User_Follows_2" ------------------------
-- CREATE LINK "lnk_User_Follows_2" ----------------------------
ALTER TABLE `Follows`
	ADD CONSTRAINT `lnk_User_Follows_2` FOREIGN KEY ( `Follower` )
	REFERENCES `User`( `username` )
	ON DELETE Cascade
	ON UPDATE Cascade;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE LINK "lnk_Post_Hashtag" --------------------------
-- CREATE LINK "lnk_Post_Hashtag" ------------------------------
ALTER TABLE `Hashtag`
	ADD CONSTRAINT `lnk_Post_Hashtag` FOREIGN KEY ( `postId` )
	REFERENCES `Post`( `postId` )
	ON DELETE Cascade
	ON UPDATE Cascade;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


-- CREATE LINK "lnk_Post_Media" ----------------------------
-- CREATE LINK "lnk_Post_Media" --------------------------------
ALTER TABLE `Media`
	ADD CONSTRAINT `lnk_Post_Media` FOREIGN KEY ( `postId` )
	REFERENCES `Post`( `postId` )
	ON DELETE Cascade
	ON UPDATE Cascade;
-- -------------------------------------------------------------
-- ---------------------------------------------------------


/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
-- ---------------------------------------------------------


