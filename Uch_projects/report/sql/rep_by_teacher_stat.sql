SELECT
    COUNT(*) AS total_projects,
    AVG(grade) AS avg_grade
FROM teacher_report
WHERE teacher_id = %s;
