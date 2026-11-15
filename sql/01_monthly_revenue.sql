-- Q1. How is revenue trending month by month, and how does each month compare with the same month last year?
WITH monthly AS (
  SELECT strftime('%Y-%m', InvoiceDate) AS month,
         ROUND(SUM(Total), 2)           AS revenue,
         COUNT(*)                       AS orders
  FROM Invoice
  GROUP BY 1
)
SELECT month,
       revenue,
       orders,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS revenue_3mo_avg,
       ROUND(100.0 * (revenue - LAG(revenue, 12) OVER (ORDER BY month)) / LAG(revenue, 12) OVER (ORDER BY month), 1) AS yoy_growth_pct
FROM monthly
ORDER BY month;
