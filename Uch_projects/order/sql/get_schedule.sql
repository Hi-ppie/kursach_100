SELECT
    cs.cs_id,
    cs.cs_date,
    cs.project_id,
    p.topic AS project_topic,
    cm.teacher_id
FROM commission_schedule cs
LEFT JOIN project p ON cs.project_id = p.project_id
LEFT JOIN commission_members cm ON cs.cs_id = cm.cs_id
ORDER BY cs.cs_date, cs.cs_id;