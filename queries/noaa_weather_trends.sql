-- Global average temperature trends by year (NOAA GSOD dataset)
-- Dataset: bigquery-public-data.noaa_gsod
SELECT
    year,
    ROUND(AVG(temp), 2) AS avg_temp_fahrenheit,
    ROUND(AVG(max), 2) AS avg_max_temp,
    ROUND(AVG(min), 2) AS avg_min_temp,
    SUM(CASE WHEN prcp > 0 AND prcp < 99.99 THEN 1 ELSE 0 END) AS rainy_days
FROM
    `bigquery-public-data.noaa_gsod.gsod*`
WHERE
    year BETWEEN '2000' AND '2022'
    AND temp != 9999.9
    AND max != 9999.9
    AND min != 9999.9
GROUP BY
    year
ORDER BY
    year ASC;
