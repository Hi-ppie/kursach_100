SELECT
    student_surname,
    project_topic,
    proj_grade  -- Исправлено
FROM teacher_report
WHERE teacher_id = %s
ORDER BY student_surname;