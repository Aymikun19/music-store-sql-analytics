-- Q3. Which genres drive sales? Revenue share and cumulative share (Pareto view).
WITH genre_rev AS (
  SELECT g.Name AS genre,
         ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue,
         SUM(il.Quantity)                          AS tracks_sold
  FROM InvoiceLine il
  JOIN Track t ON t.TrackId = il.TrackId
  JOIN Genre g ON g.GenreId = t.GenreId
  GROUP BY g.Name
)
SELECT genre,
       revenue,
       tracks_sold,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1)                                        AS share_pct,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 1)     AS cumulative_pct
FROM genre_rev
ORDER BY revenue DESC;
