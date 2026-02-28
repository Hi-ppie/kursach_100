SELECT
  project_id,
  project_topic,
  grade,
  student_surname,
  supervisor_surname
FROM project_report
WHERE CAST(r_month AS UNSIGNED) = %s
  AND CAST(r_year  AS UNSIGNED) = %s
ORDER BY project_id;