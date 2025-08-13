CREATE TABLE `User` (
	`user_id`	UUID	NOT NULL,
	`member_type`	varchar	NOT NULL	COMMENT '관리자, 고객사',
	`erterprise_id`	int	NOT NULL,
	`email`	varchar	NOT NULL,
	`name`	varchar	NOT NULL,
	`phonenumber`	int	NOT NULL,
	`personal_agreement`	boolean	NOT NULL,
	`created_at`	date	NOT NULL,
	`password`	varchar	NULL	COMMENT '암호화해서 저장'
);

CREATE TABLE `Forum` (
	`id`	int	NOT NULL	COMMENT 'auto increment',
	`user_id`	UUID	NOT NULL,
	`name`	varchar	NOT NULL,
	`title`	varchar	NOT NULL,
	`content`	varchar	NULL,
	`file_address`	varchar	NULL,
	`created_at`	date	NOT NULL,
	`updated_at`	date	NULL
);

CREATE TABLE `CostAnalysisReport` (
	`id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`address`	varchar	NOT NULL,
	`created_at`	date	NULL
);

CREATE TABLE `PanelImageReport` (
	`id`	int	NOT NULL,
	`panel_id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`status`	varchar	NOT NULL	COMMENT '손상, 오염',
	`damage_degree`	int	NULL,
	`decision`	varchar	NOT NULL	COMMENT '단순 오염, 수리, 교체',
	`request_status`	varchar	NOT NULL	COMMENT '요청 중, 요청확인, 처리중, 처리 완료',
	`created_at`	date	NOT NULL
);

CREATE TABLE `PanelImage` (
	`id`	int	NOT NULL,
	`panel_id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`film_date`	date	NOT NULL,
	`panel_imageurl`	varchar	NOT NULL,
	`is_analysis`	boolean	NOT NULL
);

CREATE TABLE `Notice` (
	`id`	int	NOT NULL	COMMENT 'auto increment',
	`user_id`	UUID	NOT NULL,
	`title`	varchar	NOT NULL,
	`content`	varchar	NOT NULL,
	`created_at`	date	NOT NULL
);

CREATE TABLE `Invoice` (
	`id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`address`	varchar	NOT NULL,
	`send_user`	UUID	NOT NULL,
	`created_at`	date	NOT NULL,
	`is_paid`	boolean	NOT NULL	DEFAULT false
);

CREATE TABLE `Panel` (
	`id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL	COMMENT '패널 소유자',
	`serial_number`	int	NOT NULL,
	`manufact_company`	varchar	NOT NULL,
	`model_name`	varchar	NOT NULL,
	`pmp_rated_w`	int	NOT NULL,
	`temp_coeff`	float	NOT NULL,
	`annual_degradation_rate`	float	NOT NULL,
	`lat`	double	NULL,
	`lon`	double	NULL,
	`installed_at`	date	NULL,
	`installed_angle`	float	NULL,
	`installed_direction`	varchar	NULL
);

CREATE TABLE `PanelManagement` (
	`id`	Integer	NOT NULL,
	`panel_status`	varchar	NOT NULL	COMMENT '정상, 오염, 파손',
	`perform_degrade`	int	NOT NULL,
	`expected_end`	date	NOT NULL,
	`damage_degree`	int	NULL,
	`is_stored`	boolean	NOT NULL	DEFAULT false,
	`start_date`	date	NULL,
	`decision_date`	date	NULL
);

CREATE TABLE `Comment` (
	`comment_id`	int	NOT NULL	COMMENT 'auto increment',
	`id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`name`	varchar	NOT NULL,
	`content`	varchar	NOT NULL,
	`created_at`	date	NOT NULL
);

CREATE TABLE `EPRDocument` (
	`id`	int	NOT NULL,
	`user_id`	UUID	NOT NULL,
	`doc_type`	varchar	NOT NULL,
	`address`	varchar	NOT NULL,
	`created_at`	date	NOT NULL,
	`submit_status`	varchar	NOT NULL
);

CREATE TABLE `PanelPerformance` (
	`id`	int	NOT NULL,
	`performance_ratio`	float	NOT NULL	COMMENT '고객사에서 제공하는 패널 성능 데이터(0~1)',
	`updated_at`	date	NULL
);

ALTER TABLE `User` ADD CONSTRAINT `PK_USER` PRIMARY KEY (
	`user_id`
);

ALTER TABLE `Forum` ADD CONSTRAINT `PK_FORUM` PRIMARY KEY (
	`id`,
	`user_id`
);

ALTER TABLE `CostAnalysisReport` ADD CONSTRAINT `PK_COSTANALYSISREPORT` PRIMARY KEY (
	`id`
);

ALTER TABLE `PanelImageReport` ADD CONSTRAINT `PK_PANELIMAGEREPORT` PRIMARY KEY (
	`id`,
	`panel_id`,
	`user_id`
);

ALTER TABLE `PanelImage` ADD CONSTRAINT `PK_PANELIMAGE` PRIMARY KEY (
	`id`,
	`panel_id`,
	`user_id`
);

ALTER TABLE `Notice` ADD CONSTRAINT `PK_NOTICE` PRIMARY KEY (
	`id`,
	`user_id`
);

ALTER TABLE `Invoice` ADD CONSTRAINT `PK_INVOICE` PRIMARY KEY (
	`id`,
	`user_id`
);

ALTER TABLE `Panel` ADD CONSTRAINT `PK_PANEL` PRIMARY KEY (
	`id`
);

ALTER TABLE `PanelManagement` ADD CONSTRAINT `PK_PANELMANAGEMENT` PRIMARY KEY (
	`id`
);

ALTER TABLE `Comment` ADD CONSTRAINT `PK_COMMENT` PRIMARY KEY (
	`comment_id`,
	`id`,
	`user_id`
);

ALTER TABLE `EPRDocument` ADD CONSTRAINT `PK_EPRDOCUMENT` PRIMARY KEY (
	`id`,
	`user_id`
);

ALTER TABLE `PanelPerformance` ADD CONSTRAINT `PK_PANELPERFORMANCE` PRIMARY KEY (
	`id`
);

ALTER TABLE `Forum` ADD CONSTRAINT `FK_User_TO_Forum_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `User` (
	`user_id`
);

ALTER TABLE `PanelImageReport` ADD CONSTRAINT `FK_PanelImage_TO_PanelImageReport_1` FOREIGN KEY (
	`id`
)
REFERENCES `PanelImage` (
	`id`
);

ALTER TABLE `PanelImageReport` ADD CONSTRAINT `FK_PanelImage_TO_PanelImageReport_2` FOREIGN KEY (
	`panel_id`
)
REFERENCES `PanelImage` (
	`panel_id`
);

ALTER TABLE `PanelImageReport` ADD CONSTRAINT `FK_PanelImage_TO_PanelImageReport_3` FOREIGN KEY (
	`user_id`
)
REFERENCES `PanelImage` (
	`user_id`
);

ALTER TABLE `PanelImage` ADD CONSTRAINT `FK_Panel_TO_PanelImage_1` FOREIGN KEY (
	`panel_id`
)
REFERENCES `Panel` (
	`id`
);

ALTER TABLE `PanelImage` ADD CONSTRAINT `FK_User_TO_PanelImage_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `User` (
	`user_id`
);

ALTER TABLE `Notice` ADD CONSTRAINT `FK_User_TO_Notice_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `User` (
	`user_id`
);

ALTER TABLE `Invoice` ADD CONSTRAINT `FK_User_TO_Invoice_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `User` (
	`user_id`
);

ALTER TABLE `PanelManagement` ADD CONSTRAINT `FK_Panel_TO_PanelManagement_1` FOREIGN KEY (
	`id`
)
REFERENCES `Panel` (
	`id`
);

ALTER TABLE `Comment` ADD CONSTRAINT `FK_Forum_TO_Comment_1` FOREIGN KEY (
	`id`
)
REFERENCES `Forum` (
	`id`
);

ALTER TABLE `Comment` ADD CONSTRAINT `FK_Forum_TO_Comment_2` FOREIGN KEY (
	`user_id`
)
REFERENCES `Forum` (
	`user_id`
);

ALTER TABLE `EPRDocument` ADD CONSTRAINT `FK_User_TO_EPRDocument_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `User` (
	`user_id`
);

ALTER TABLE `PanelPerformance` ADD CONSTRAINT `FK_Panel_TO_PanelPerformance_1` FOREIGN KEY (
	`id`
)
REFERENCES `Panel` (
	`id`
);

