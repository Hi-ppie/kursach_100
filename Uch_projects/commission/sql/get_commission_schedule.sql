SELECT
    cs.cs_id,
    cs.cs_date,
    cs.project_id,
    p.topic AS project_topic,
    d.name AS discipline_name,
    s.surname AS student_surname,
    t_sup.surname AS supervisor_surname,
    t_comm.surname AS teacher_surname
FROM commission_schedule cs
JOIN project p ON cs.project_id = p.project_id
LEFT JOIN discipline d ON p.discipline_id = d.discipline_id
LEFT JOIN student s ON p.student_id = s.student_id
LEFT JOIN teacher t_sup ON p.supervisor_id = t_sup.teacher_id
LEFT JOIN commission_members cm ON cs.cs_id = cm.cs_id
LEFT JOIN teacher t_comm ON cm.teacher_id = t_comm.teacher_id
ORDER BY cs.cs_date, cs.cs_id, t_comm.surname;