SELECT DISTINCT
    p.project_id,
    p.topic,
    p.grade,
    p.defense_date,
    s.surname AS student_surname
FROM teacher t
JOIN commission_members cm ON cm.teacher_id = t.teacher_id
JOIN commission_schedule cs ON cs.cs_id = cm.cs_id
JOIN defense d ON d.project_id = p.project_id
JOIN project p ON p.project_id = d.project_id
JOIN student s ON p.student_id = s.student_id
WHERE t.surname = %s;
