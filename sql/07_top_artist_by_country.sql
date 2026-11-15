-- Q7. What is the best-selling artist in each of the top markets?
WITH artist_country AS (
  SELECT i.BillingCountry AS country, ar.Name AS artist, SUM(il.Quantity) AS tracks_sold
  FROM InvoiceLine il
  JOIN Invoice i ON i.InvoiceId = il.InvoiceId
  JOIN Track   t ON t.TrackId   = il.TrackId
  JOIN Album  al ON al.AlbumId  = t.AlbumId
  JOIN Artist ar ON ar.ArtistId = al.ArtistId
  GROUP BY 1, 2
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY country ORDER BY tracks_sold DESC, artist) AS rn
  FROM artist_country
)
SELECT country, artist, tracks_sold
FROM ranked
WHERE rn = 1 AND country IN (SELECT BillingCountry FROM Invoice GROUP BY 1 ORDER BY SUM(Total) DESC LIMIT 8)
ORDER BY tracks_sold DESC;
