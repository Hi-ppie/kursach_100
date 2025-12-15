SELECT
    project_id,
    topic,
    grade,
    defense_date
FROM project
WHERE topic LIKE %s;
