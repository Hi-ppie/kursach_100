SELECT
    COUNT(*) AS total,
    AVG(grade) AS avg_grade,
    SUM(CASE WHEN grade = 5 THEN 1 ELSE 0 END) AS count_fives
FROM project_report
WHERE r_month = %s AND r_year = %s;
