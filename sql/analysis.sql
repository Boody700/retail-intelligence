-- SQLite queries against data/retail.sqlite. SalesPence is integer currency.
-- All records in sales have passed the sequential cleaning waterfall.

-- 1. Headline performance: positive merchandise sales, not net revenue.
SELECT ROUND(SUM(SalesPence) / 100.0, 2) AS merchandise_sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       COUNT(DISTINCT CustomerID) AS identified_buyers,
       ROUND(SUM(SalesPence) / 100.0 / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value_gbp
FROM sales;

-- 2. Monthly trend. Final December is partial and flagged explicitly.
SELECT Month, ROUND(SUM(SalesPence) / 100.0, 2) AS sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders,
       CASE WHEN Month = (SELECT MAX(Month) FROM sales) THEN 1 ELSE 0 END AS final_partial_month
FROM sales GROUP BY Month ORDER BY Month;

-- 3. Market concentration; share denominator includes all countries.
WITH markets AS (
  SELECT Country, SUM(SalesPence) AS pence FROM sales GROUP BY Country
)
SELECT Country, ROUND(pence / 100.0, 2) AS sales_gbp,
       ROUND(100.0 * pence / SUM(pence) OVER (), 2) AS sales_share_pct
FROM markets ORDER BY pence DESC;

-- 4. Product rankings by stable SKU (names can vary over time).
SELECT StockCode, SUM(Quantity) AS units,
       COUNT(DISTINCT InvoiceNo) AS order_appearances,
       ROUND(SUM(SalesPence) / 100.0, 2) AS sales_gbp
FROM sales GROUP BY StockCode ORDER BY SUM(SalesPence) DESC LIMIT 20;

-- 5. Customer RFM. Keep customers without IDs out of buyer-level metrics.
SELECT CustomerID,
       CAST(julianday('2011-12-10') - julianday(date(MAX(InvoiceDate))) AS INTEGER) AS recency_days,
       COUNT(DISTINCT InvoiceNo) AS frequency,
       ROUND(SUM(SalesPence) / 100.0, 2) AS monetary_gbp
FROM sales WHERE CustomerID IS NOT NULL GROUP BY CustomerID;

-- 6. Repeat-purchase share, based on invoices rather than line count.
WITH frequency AS (
  SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS orders
  FROM sales WHERE CustomerID IS NOT NULL GROUP BY CustomerID
)
SELECT COUNT(*) AS buyers, SUM(orders > 1) AS repeat_buyers,
       ROUND(100.0 * SUM(orders > 1) / COUNT(*), 2) AS repeat_share_pct
FROM frequency;

-- 7. Cohort repeat activity in complete months; explicit zero cells.
WITH buyer_months AS (
  SELECT DISTINCT CustomerID, Month FROM sales WHERE CustomerID IS NOT NULL
), cohorts AS (
  SELECT CustomerID, MIN(Month) AS cohort FROM buyer_months GROUP BY CustomerID
), calendar AS (
  SELECT DISTINCT Month FROM sales WHERE Month < (SELECT MAX(Month) FROM sales)
), sizes AS (
  SELECT cohort, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort
)
SELECT s.cohort, m.Month,
       (CAST(substr(m.Month,1,4) AS INTEGER)-CAST(substr(s.cohort,1,4) AS INTEGER))*12
        + CAST(substr(m.Month,6,2) AS INTEGER)-CAST(substr(s.cohort,6,2) AS INTEGER) AS month_age,
       s.cohort_size, COUNT(b.CustomerID) AS active_buyers,
       ROUND(1.0 * COUNT(b.CustomerID) / s.cohort_size, 5) AS repeat_activity
FROM sizes s JOIN calendar m ON m.Month >= s.cohort
JOIN cohorts c ON c.cohort=s.cohort
LEFT JOIN buyer_months b ON b.CustomerID=c.CustomerID AND b.Month=m.Month
GROUP BY s.cohort,m.Month,s.cohort_size ORDER BY s.cohort,m.Month;
