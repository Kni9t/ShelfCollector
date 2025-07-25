SELECT
  sh.name AS shelf_name,
  substr(s.date, 1, 7) AS month,
  SUM(s.revenue) AS total_revenue
FROM
  sales s
JOIN
  shelves sh ON s.shelf_id = sh.shelf_id
GROUP BY
  sh.name, month
ORDER BY
  month, shelf_name;