SELECT
    student_surname,
    project_topic,
    grade
FROM teacher_report
WHERE teacher_id = %s
ORDER BY student_surname;
