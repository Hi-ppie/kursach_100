SELECT
    COUNT(*) AS total_projects,
    AVG(proj_grade) AS avg_grade  -- ← proj_grade
FROM teacher_report
WHERE teacher_id = %s;