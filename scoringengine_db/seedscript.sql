#Created by: Katelyn Valles
#MariaDB


CREATE OR REPLACE SCHEMA innodb;


#Created by: Katelyn Valles
#MariaDB

CREATE OR REPLACE TABLE User
(
	userId int unsigned NOT NULL AUTO_INCREMENT,
	username varchar(45) NULL,
	roleId int NULL,
	passwordHash varchar(254) NULL,
    	UNIQUE KEY `id` (`userId`)
);


CREATE OR REPLACE TABLE Phase 
(
	phaseId int unsigned NOT NULL AUTO_INCREMENT,
	name varchar(45) unique NOT NULL,
    UNIQUE KEY `id` (`phaseId`)
);

CREATE OR REPLACE TABLE Artifact
(
	artifactId int unsigned NOT NULL AUTO_INCREMENT,
	userId int unsigned NOT NULL,
	phaseId int unsigned NULL,
	phaseArtifactId int unsigned NOT NULL,
   	artifactName  varchar(45) NULL,
	artifactType varchar(45) NULL,
	artifactString varchar(254) NULL,
	difficulty varchar(45) NULL,
	notes varchar(254) NULL,
    	UNIQUE KEY `id` (`artifactId`),
    	UNIQUE KEY `artifact_phase_unique` (`phaseId`,`phaseArtifactId`),
    	CONSTRAINT `fk_phaseId` FOREIGN KEY (`phaseId`) REFERENCES `Phase` (`phaseId`) ON DELETE SET NULL,
    	CONSTRAINT `fk_userId` FOREIGN KEY (`userId`) REFERENCES `User` (`userId`)  ON DELETE CASCADE
);
 

CREATE OR REPLACE TABLE Role
(
	roleId int unsigned NOT NULL,
	description varchar(255) NOT NULL,
    UNIQUE KEY `id` (`roleId`)
);


CREATE OR REPLACE TABLE UserArtifactSubmission
(
	userArtifactSubmissionId int unsigned NOT NULL AUTO_INCREMENT,
	userId int unsigned NOT NULL,
	submissionString varchar(254) NULL,
    updatedTimeStamp DATETIME NOT NULL DEFAULT NOW(),
    UNIQUE KEY `id` (`userArtifactSubmissionId`)
);

INSERT INTO User(username,passwordHash,roleId)
VALUES 
('sample_assessor','HUSfwlUinwfuhqph',2),
('cyberteam1','VcZyWEwUmuiJFPpP',1),
('pizzateam','ErwzUSXHleWpnKVZ',2),
('chronosteam','bmEyGxJsilkVbROC',0),
('pirateteam','WgtrkrWgBWKPXmGL',0),
('ninjateam','moFaaTdSTUlVPePb',1),
('soldiercyberteam','OisuYcjWysUtxGyO',2),
('azcyberteam','HbAQqFrzaYoutCKL',0),
('zeldateam','PIguKCxvuENaBHUs',2),
('titanteam','MiDlInPRShrRTdve',1),
('slayerteam','qvsRxhpFLmNRWpBr',0),
('skullcrushersteam','fborArNPvLEQPgSH',1),
('midgardteam','FKrLUfHQPoBFdXlx',2),
('teseractteam','bwCjteTEzIaVjUuv',1);

INSERT INTO Role (roleId,description)
VALUES 
(2,'admin'),
(1,'assessor'),
(0,'team');


INSERT INTO UserArtifactSubmission(userId,submissionString, updatedTimeStamp)
VALUES
(1,'evil.exe', '2021-10-17 04:36:56.000'),
(2,'129.130.112.13', '2021-10-17 04:36:56.000'),
(3,'www[.]evil[.]com', '2021-10-17 04:36:56.000'),
(4,'C:\users\user1\documents','2021-10-17 04:36:56.000'),
(5,'/usr/bin/evil.sh','2021-10-17 04:36:56.000'),
(6,'hxxp://www[.]evil[.].com/evil[.]js','2021-10-17 04:36:56.000'),
(7,'c7b6787641fbf45ca30726072bc4bfcf','2021-10-17 04:36:56.000'),
(8,'3C68C0A4542575FF4D7EADA9B35995647EF5EDE01AB8241D2A3B92BE57407CCA', '2021-10-17 04:36:56.000'),
(9,'leroyjenkins','2021-10-17 04:36:56.000'),
(10,'5554', '2021-10-17 04:36:56.000'),
(11,'129.130.112.76:5554', '2021-10-17 04:36:56.000'),
(12,'2345:0425:2CA1:0000:0000:0567:5673:23b5', '2021-10-17 04:36:56.000'),
(13,'2345:0425:2CA1:0000:0000:0567:5673:23b5:5554', '2021-10-17 04:36:56.000'),
(14,'RDP', '2021-10-17 04:36:56.000'),
(15,'VNC', '2021-10-17 04:36:56.000');

INSERT INTO Phase (name)
VALUES
('first phase'),
('second phase'),
('third phase');


INSERT INTO Artifact (userId, phaseId,phaseArtifactId,artifactName,artifactType,artifactString,difficulty,notes)
VALUES 
(2,1,1,'kiwi','File Name','good.exe','easy',NULL),
(13,1,2,'lime','IPv4 Address','129.130.112.14','medium',NULL),
(5,2,1,'apple','Domain','www[.]evil[.]com','medium','Domain is defanged, need to support this!'),
(8,3,1,'strawberry','File Path','C:\users\user2\documents','hard','Windows file path'),
(11,2,2,'raspberry','File Path','/usr/bin/evil.sh','easy','Linux file path'),
(3,1,3,'mango','URL','hxxp://www[.]evil[.].com/evil[.]js','hard','Defanged full path URL'),
(9,1,4,'spinach','Hash','c7b6787641fbf45ca30726072bc4bfcf','medium','MD5 Hash'),
(8,2,3,'blueberry','Hash','3C68C0A4542575FF4D7EADA9B35E95647EF5EDE01AB8241D2A3B92BE57407CCA','easy',NULL),
(6,3,2,'banana','Username','ler0yjenkins','medium',NULL),
(5,2,4,'peach','TCP/UDP Port','55547','hard','Example port (Sasser Worm)'),
(12,1,5,'pear','Socket','129.130.112.76:5554','easy','IPv4 address + TCP/UDP Port'),
(5,1,6,'lemon','IPv6 Address','2345:0425:2CA1:0000:0000:0567:5673:23b5','easy',NULL),
(3,3,3,'kale','Socket','2345:0425:2CA1:0000:0000:0567:5673:23b5:5554','hard','IPv6 address + TCP/UDP Port)'),
(9,2,5,'romaine','Protocol/Service Name','RDP','medium','Windows Remote Access)'),
(14,3,4,'tomato','Protocol/Service Name','VNCX','medium','Linux Remote Access');
