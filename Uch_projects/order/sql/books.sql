SELECT project_id, topic, grade,
(CASE WHEN EXISTS (SELECT 1 FROM commission_schedule WHERE project_id = p.project_id) THEN 1 ELSE 0 END) as has_commission
FROM project p WHERE student_id = (%s)