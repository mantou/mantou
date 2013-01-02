CREATE TABLE `douban_rate` (
  `douban_rate_id` int(11) NOT NULL,
  `category` varchar(20) DEFAULT NULL,
  `name` varchar(45) NOT NULL,
  `rate` decimal(3,1) DEFAULT NULL,
  `country` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`douban_rate_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8$$

