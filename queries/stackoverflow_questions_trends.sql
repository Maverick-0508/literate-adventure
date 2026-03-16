-- Stack Overflow question trends by year and top tags
-- Dataset: bigquery-public-data.stackoverflow
SELECT
    EXTRACT(YEAR FROM creation_date) AS question_year,
    COUNT(*) AS total_questions,
    AVG(score) AS avg_score,
    AVG(answer_count) AS avg_answers,
    AVG(view_count) AS avg_views
FROM
    `bigquery-public-data.stackoverflow.posts_questions`
WHERE
    creation_date IS NOT NULL
    AND EXTRACT(YEAR FROM creation_date) BETWEEN 2010 AND 2022
GROUP BY
    question_year
ORDER BY
    question_year ASC;
