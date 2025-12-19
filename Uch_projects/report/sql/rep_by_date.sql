SELECT
    project_id,
    project_topic,
    grade,
    student_surname,
    supervisor_surname
FROM project_report
WHERE CAST(r_month AS UNSIGNED) = %s
  AND CAST(r_year AS UNSIGNED) = %s
ORDER BY project_id;

SELECT
    COUNT(*) AS total,
    AVG(CASE
        WHEN grade = 'Excellent' THEN 5
        WHEN grade = 'Good' THEN 4
        WHEN grade = 'Sat' THEN 3
        ELSE 0
    END) AS avg_grade,
    SUM(CASE WHEN grade = 'Excellent' THEN 1 ELSE 0 END) AS count_excellent  -- Изменено на count_excellent, т.к. 'Excellent' эквивалент 5
FROM project_report
WHERE r_month = %s AND r_year = %s;