SELECT topic(3) as deviceid, parse_time("yyyy-MM-dd'T'HH:mm:ss.sss'Z'", timestamp()) AS timestamp, * FROM 'vt/cvra/#'
