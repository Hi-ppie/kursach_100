SELECT
    p.project_id,
    p.topic,
    p.grade,
    p.defense_date,
    p.student_id,
    p.supervisor_id,
    s.surname AS student_surname,
    t.surname AS supervisor_surname,
    (CASE WHEN EXISTS (SELECT 1 FROM commission_schedule WHERE project_id = p.project_id) THEN 1 ELSE 0 END) as has_commission
FROM project p
JOIN student s ON p.student_id = s.student_id
JOIN teacher t ON p.supervisor_id = t.teacher_id
WHERE p.discipline_id = (%s)
ORDER BY p.project_id;