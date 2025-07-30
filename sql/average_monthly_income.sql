SELECT 
  AVG(monthly_revenue) AS average_monthly_revenue
FROM (
  SELECT 
    strftime('%Y-%m', date) AS month,
    SUM(revenue) AS monthly_revenue
  FROM sales
  WHERE strftime('%Y', date) = '2025'
  GROUP BY month
) AS monthly_totals;
