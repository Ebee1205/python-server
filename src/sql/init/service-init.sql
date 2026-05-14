-- service initial schema
-- Target: MySQL 8.0+ (utf8mb4)

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS tb_user (
	id BIGINT NOT NULL AUTO_INCREMENT,
	email VARCHAR(255) NOT NULL,
	password VARCHAR(255) NULL,
	name VARCHAR(100) NULL,
	nickname VARCHAR(100) NULL,
	phone VARCHAR(20) NULL,
	emailConf VARCHAR(1) NOT NULL DEFAULT '2',
	`desc` TEXT NULL,
	fileId VARCHAR(255) NULL,
	role ENUM('SUPER_ADMIN', 'ADMIN', 'CLIENT') NOT NULL DEFAULT 'CLIENT',
	state INT NOT NULL DEFAULT 1,
	extra JSON NULL,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uk_tb_user_email (email),
	KEY idx_tb_user_state (state),
	CONSTRAINT ck_tb_user_state CHECK (state IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_img_ctg (
	id BIGINT NOT NULL AUTO_INCREMENT,
	name VARCHAR(100) NOT NULL,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_tag (
	id BIGINT NOT NULL AUTO_INCREMENT,
	userId BIGINT NOT NULL,
	parentCode VARCHAR(50) NULL,
	code VARCHAR(50) NOT NULL,
	tagName VARCHAR(100) NOT NULL,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uk_tb_tag_code (code),
	KEY idx_tb_tag_userId (userId),
	CONSTRAINT fk_tb_tag_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_img (
	id BIGINT NOT NULL AUTO_INCREMENT,
	userId BIGINT NOT NULL,
	ctgId BIGINT NOT NULL,
	imgUrl VARCHAR(500) NOT NULL,
	title VARCHAR(200) NULL,
	`desc` TEXT NULL,
	useCnt INT NOT NULL DEFAULT 0,
	kwd JSON NULL,
	aiDocId VARCHAR(100) NULL,
	expWeight FLOAT NOT NULL DEFAULT 0,
	pri INT NOT NULL DEFAULT 0,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	KEY idx_tb_img_userId (userId),
	KEY idx_tb_img_ctgId (ctgId),
	KEY idx_tb_img_rank (useCnt, expWeight, pri),
	CONSTRAINT fk_tb_img_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT fk_tb_img_ctgId FOREIGN KEY (ctgId) REFERENCES tb_img_ctg (id)
		ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_session (
	id BIGINT NOT NULL,
	userId BIGINT NOT NULL,
	imgId BIGINT NOT NULL,
	sDate BIGINT NOT NULL,
	eDate BIGINT NULL,
	device JSON NULL,
	sStat INT NOT NULL DEFAULT 0,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	KEY idx_tb_session_userId (userId),
	KEY idx_tb_session_imgId (imgId),
	KEY idx_tb_session_status_date (sStat, sDate),
	CONSTRAINT fk_tb_session_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT fk_tb_session_imgId FOREIGN KEY (imgId) REFERENCES tb_img (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT ck_tb_session_sStat CHECK (sStat IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_prod (
	id BIGINT NOT NULL AUTO_INCREMENT,
	userId BIGINT NOT NULL,
	name VARCHAR(200) NOT NULL,
	brand VARCHAR(300) NULL,
	price INT NOT NULL DEFAULT 0,
	thumbUrl VARCHAR(500) NULL,
	pStat INT NOT NULL DEFAULT 1,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	KEY idx_tb_prod_userId (userId),
	KEY idx_tb_prod_pStat (pStat),
	CONSTRAINT fk_tb_prod_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT ck_tb_prod_pStat CHECK (pStat IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS tb_snap (
	id BIGINT NOT NULL AUTO_INCREMENT,
	userId BIGINT NOT NULL,
	prodId BIGINT NOT NULL,
	imgId BIGINT NOT NULL,
	sId BIGINT NULL,
	snapUrl VARCHAR(500) NOT NULL,
	comment TEXT NULL,
	gender INT NOT NULL DEFAULT 0,
	userH FLOAT NULL,
	userW FLOAT NULL,
	viewCnt INT NOT NULL DEFAULT 0,
	cDate BIGINT NOT NULL,
	uDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	KEY idx_tb_snap_userId (userId),
	KEY idx_tb_snap_prodId (prodId),
	KEY idx_tb_snap_imgId (imgId),
	UNIQUE KEY uk_tb_snap_sId (sId),
	KEY idx_tb_snap_viewCnt (viewCnt),
	CONSTRAINT fk_tb_snap_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT fk_tb_snap_prodId FOREIGN KEY (prodId) REFERENCES tb_prod (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT fk_tb_snap_imgId FOREIGN KEY (imgId) REFERENCES tb_img (id)
		ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT fk_tb_snap_sId FOREIGN KEY (sId) REFERENCES tb_session (id)
		ON DELETE SET NULL ON UPDATE CASCADE,
	CONSTRAINT ck_tb_snap_gender CHECK (gender IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS mtb_bookmark (
	id BIGINT NOT NULL AUTO_INCREMENT,
	userId BIGINT NOT NULL,
	imgId BIGINT NOT NULL,
	cDate BIGINT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uk_mtb_bookmark_user_img (userId, imgId),
	KEY idx_mtb_bookmark_userId (userId),
	KEY idx_mtb_bookmark_imgId (imgId),
	CONSTRAINT fk_mtb_bookmark_userId FOREIGN KEY (userId) REFERENCES tb_user (id)
		ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_mtb_bookmark_imgId FOREIGN KEY (imgId) REFERENCES tb_img (id)
		ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS mtb_img_tag (
	id BIGINT NOT NULL AUTO_INCREMENT,
	imgId BIGINT NOT NULL,
	tagId BIGINT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uk_mtb_img_tag_img_tag (imgId, tagId),
	KEY idx_mtb_img_tag_imgId (imgId),
	KEY idx_mtb_img_tag_tagId (tagId),
	CONSTRAINT fk_mtb_img_tag_imgId FOREIGN KEY (imgId) REFERENCES tb_img (id)
		ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_mtb_img_tag_tagId FOREIGN KEY (tagId) REFERENCES tb_tag (id)
		ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
