SELECT sh.name AS shelf_name, SUM(s.revenue) AS total_revenue
FROM sales s
join shelves sh on s.shelf_id = sh.shelf_id
GROUP BY sh.name;