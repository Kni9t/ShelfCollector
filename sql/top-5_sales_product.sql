SELECT name AS product_name,
       SUM(count) AS total_sales,
       SUM(revenue) AS total_revenue
FROM sales
GROUP BY name
ORDER by total_sales DESC
LIMIT 5;