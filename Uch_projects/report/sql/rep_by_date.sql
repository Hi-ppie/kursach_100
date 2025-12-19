SELECT
    project_id,
    project_topic,
    grade,
    student_surname,
    supervisor_surname
FROM project_report
WHERE r_month = %s AND r_year = %s
ORDER BY project_id;

SELECT
    COUNT(*) AS total,
    AVG(grade) AS avg_grade,
    SUM(CASE WHEN grade = 5 THEN 1 ELSE 0 END) AS count_fives
FROM project_report
WHERE r_month = %s AND r_year = %s;
