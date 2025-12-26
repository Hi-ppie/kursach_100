SELECT DISTINCT cm.teacher_id
FROM commission_members cm
JOIN commission_schedule cs ON cm.cs_id = cs.cs_id
WHERE cs.cs_date = (%s);