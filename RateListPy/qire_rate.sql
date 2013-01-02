CREATE TABLE `qire_rate` (

  `qire_rate_id` int(11) NOT NULL AUTO_INCREMENT,

  `category` varchar(20) DEFAULT NULL,

  `page_id` int(11) NOT NULL,

  `rate` decimal(3,1) DEFAULT NULL,

  `name` varchar(45) NOT NULL,

  `link` varchar(200) DEFAULT NULL,

  `format` varchar(200) DEFAULT NULL,

  PRIMARY KEY (`qire_rate_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8