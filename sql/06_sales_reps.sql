-- Q6. How do support reps compare on the revenue of the customers they manage?
SELECT e.FirstName || ' ' || e.LastName          AS rep,
       e.Title                                    AS title,
       COUNT(DISTINCT c.CustomerId)               AS customers,
       ROUND(SUM(i.Total), 2)                     AS revenue,
       ROUND(SUM(i.Total) / COUNT(DISTINCT c.CustomerId), 2) AS revenue_per_customer,
       RANK() OVER (ORDER BY SUM(i.Total) DESC)   AS revenue_rank
FROM Employee e
JOIN Customer c ON c.SupportRepId = e.EmployeeId
JOIN Invoice  i ON i.CustomerId   = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY revenue DESC;
