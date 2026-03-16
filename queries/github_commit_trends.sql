-- GitHub commit activity trends by year
-- Dataset: bigquery-public-data.github_repos
SELECT
    EXTRACT(YEAR FROM committer.date) AS commit_year,
    COUNT(*) AS total_commits
FROM
    `bigquery-public-data.github_repos.commits`
WHERE
    committer.date IS NOT NULL
    AND EXTRACT(YEAR FROM committer.date) BETWEEN 2010 AND 2022
GROUP BY
    commit_year
ORDER BY
    commit_year ASC;
