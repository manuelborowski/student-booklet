--
-- Dumping routines for database 'student_booklet_db'
--
/*!50003 DROP FUNCTION IF EXISTS `concat_remark_measures` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `concat_remark_measures`(id INT) RETURNS varchar(1024) CHARSET utf8
BEGIN
	DECLARE topic VARCHAR(1024);
	DECLARE note VARCHAR(1024);
	SELECT GROUP_CONCAT(measure_topics.topic SEPARATOR ', ') INTO topic
	FROM remarks
	JOIN remark_measures ON remark_measures.remark_id = remarks.id JOIN measure_topics ON measure_topics.id = remark_measures.topic_id
    WHERE remarks.id = id;
	select remarks.measure_note INTO note FROM remarks WHERE remarks.id = id;
    RETURN CONCAT(IFNULL(CONCAT(topic, ', '), ''), note);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `concat_remark_subjects` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `concat_remark_subjects`(id INT) RETURNS varchar(1024) CHARSET utf8
BEGIN
	DECLARE topic VARCHAR(1024);
    DECLARE note VARCHAR(1024);
	SELECT GROUP_CONCAT(subject_topics.topic SEPARATOR ', ') INTO topic
	FROM remarks
	JOIN remark_subjects ON remark_subjects.remark_id = remarks.id JOIN subject_topics ON subject_topics.id = remark_subjects.topic_id
    WHERE remarks.id = id;
	#group by remarks.id;
    SELECT remarks.subject_note INTO note FROM remarks WHERE remarks.id = id;
    RETURN CONCAT(IFNULL(CONCAT(topic, ', '), ''), note);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `nbr_of_remarks` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `nbr_of_remarks`(id int) RETURNS int(11)
BEGIN
	DECLARE nbr INT;
	SELECT COUNT(students.id) INTO nbr
	FROM students
	JOIN remarks ON remarks.student_id = students.id
	WHERE students.id = id;
	RETURN nbr;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

-- Dump completed
