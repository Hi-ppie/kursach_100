SELECT cm.teacher_id, t.surname, t.account_num FROM commission_members cm
JOIN commission_schedule cs ON cm.cs_id = cs.cs_id
JOIN teacher t ON cm.teacher_id = t.teacher_id
WHERE cs.project_id = (%s)