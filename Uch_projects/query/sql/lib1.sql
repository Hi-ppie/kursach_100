SELECT
    p.project_id,
    p.topic,
    p.grade,
    p.defense_date,
    s.surname AS student_surname,
    t.surname AS supervisor_surname
FROM project p
JOIN student s ON p.student_id = s.student_id
JOIN teacher t ON p.supervisor_id = t.teacher_id
WHERE p.defense_date = %s;
