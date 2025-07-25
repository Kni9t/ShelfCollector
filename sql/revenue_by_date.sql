SELECT SUM(s.revenue) AS total_revenue, s.date
FROM sales s
GROUP BY s.date;