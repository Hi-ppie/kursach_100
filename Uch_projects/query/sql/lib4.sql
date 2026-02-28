SELECT
  project_id,
  topic,
  grade,
  defense_date
FROM project
WHERE
  (
    -- Если передан положительный project_id (>0) — выполняем точный поиск
    (%s > 0 AND (project_id = %s OR topic = %s))
    -- Иначе выполняем поиск по подстроке
    OR (%s <= 0 AND topic LIKE %s)
  )
ORDER BY project_id;