-- Hacker News story submission trends by year
-- Dataset: bigquery-public-data.hacker_news
SELECT
    EXTRACT(YEAR FROM timestamp) AS story_year,
    COUNT(*) AS total_stories,
    AVG(score) AS avg_score,
    AVG(descendants) AS avg_comments
FROM
    `bigquery-public-data.hacker_news.stories`
WHERE
    timestamp IS NOT NULL
    AND EXTRACT(YEAR FROM timestamp) BETWEEN 2010 AND 2022
GROUP BY
    story_year
ORDER BY
    story_year ASC;
