-- Q2. Which countries bring in the most revenue, and do they have more customers or bigger baskets?
SELECT i.BillingCountry                                  AS country,
       COUNT(DISTINCT i.CustomerId)                      AS customers,
       COUNT(*)                                          AS orders,
       ROUND(SUM(i.Total), 2)                            AS revenue,
       ROUND(SUM(i.Total) / COUNT(DISTINCT i.CustomerId), 2) AS revenue_per_customer,
       ROUND(AVG(i.Total), 2)                            AS avg_order_value,
       ROUND(100.0 * SUM(i.Total) / SUM(SUM(i.Total)) OVER (), 1) AS revenue_share_pct
FROM Invoice i
GROUP BY i.BillingCountry
ORDER BY revenue DESC
LIMIT 10;
