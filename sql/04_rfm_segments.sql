-- Q4. RFM segmentation: who are our champions, and who is slipping away?
-- Recency is measured against the last invoice date in the data.
WITH last_date AS (SELECT MAX(julianday(InvoiceDate)) AS d FROM Invoice),
rfm AS (
  SELECT c.CustomerId,
         c.FirstName || ' ' || c.LastName                                AS customer,
         c.Country                                                       AS country,
         CAST((SELECT d FROM last_date) - MAX(julianday(i.InvoiceDate)) AS INT) AS recency_days,
         COUNT(i.InvoiceId)                                              AS frequency,
         ROUND(SUM(i.Total), 2)                                          AS monetary
  FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId
  GROUP BY c.CustomerId
),
scored AS (
  SELECT *,
         NTILE(4) OVER (ORDER BY recency_days DESC) AS r,   -- 4 = most recent
         NTILE(4) OVER (ORDER BY frequency)         AS f,
         NTILE(4) OVER (ORDER BY monetary)          AS m
  FROM rfm
)
SELECT customer, country, recency_days, frequency, monetary, r, f, m,
       CASE
         WHEN r >= 3 AND m = 4             THEN 'Champion'
         WHEN r >= 3 AND m >= 2            THEN 'Loyal'
         WHEN r <= 2 AND m >= 3            THEN 'At risk (high value)'
         WHEN r = 1                        THEN 'Hibernating'
         ELSE 'Needs attention'
       END AS segment
FROM scored
ORDER BY monetary DESC;
