USE `student_booklet_db`;
DROP function IF EXISTS `nbr_of_remarks`;

DELIMITER $$
USE `student_booklet_db`$$
CREATE DEFINER=`root`@`localhost` FUNCTION `nbr_of_remarks`(id int) RETURNS int(11)
BEGIN
	DECLARE nbr INT;
	SELECT COUNT(students.id) INTO nbr
	FROM students
	JOIN remarks ON remarks.student_id = students.id
	WHERE students.id = id;
	RETURN nbr;
END$$

DELIMITER ;


USE `student_booklet_db`;
DROP function IF EXISTS `concat_remark_measures`;

DELIMITER $$
USE `student_booklet_db`$$
CREATE FUNCTION `concat_remark_measures`(id INT) RETURNS varchar(1024) CHARSET utf8
BEGIN
	DECLARE topic VARCHAR(1024);
	SELECT GROUP_CONCAT(measure_topics.topic, ', ', remarks.measure_note SEPARATOR ', ') INTO topic
	FROM remarks
	JOIN remark_measures ON remark_measures.remark_id = remarks.id JOIN measure_topics ON measure_topics.id = remark_measures.topic_id
    WHERE remarks.id = id
	group by remarks.id;
    RETURN topic;
END$$

DELIMITER ;


