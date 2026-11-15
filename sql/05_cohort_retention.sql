-- Q5. Cohort retention: of customers whose first purchase was in year Y, what share bought again in each later year?
WITH first_purchase AS (
  SELECT CustomerId, MIN(strftime('%Y', InvoiceDate)) AS cohort FROM Invoice GROUP BY CustomerId
),
activity AS (
  SELECT DISTINCT i.CustomerId, fp.cohort, strftime('%Y', i.InvoiceDate) AS year
  FROM Invoice i JOIN first_purchase fp USING (CustomerId)
)
SELECT cohort,
       year,
       CAST(year AS INT) - CAST(cohort AS INT)                                AS years_since_first,
       COUNT(*)                                                               AS active_customers,
       ROUND(100.0 * COUNT(*) / FIRST_VALUE(COUNT(*)) OVER (PARTITION BY cohort ORDER BY year), 1) AS retention_pct
FROM activity
GROUP BY cohort, year
ORDER BY cohort, year;
