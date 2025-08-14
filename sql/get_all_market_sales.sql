SELECT
  m.market_id,
  m.name AS market_name,
  SUM(CASE WHEN s.cash IN (1, '1', 't', 'true', 'True')  THEN s.revenue ELSE 0 END) AS revenue_cash,
  SUM(CASE WHEN s.cash IN (0, '0', 'f', 'false', 'False') THEN s.revenue ELSE 0 END) AS revenue_noncash,
  SUM(COALESCE(s.revenue,0)) AS revenue_total
FROM markets AS m
LEFT JOIN market_sales AS s
  ON s.market_id = m.market_id
GROUP BY m.market_id, m.name
ORDER BY m.market_id;
