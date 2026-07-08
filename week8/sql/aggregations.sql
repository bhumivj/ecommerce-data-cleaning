-- aggregations.sql
-- Basic Queries (1-3) and Intermediate Queries (4-6)

-- =========================================================
-- 1. Total revenue per category
--    revenue = quantity * unit_price * (1 - discount_percent/100)
-- =========================================================
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- =========================================================
-- 2. Top 10 customers by total order value
-- =========================================================
SELECT
    o.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id IS NOT NULL
GROUP BY o.customer_id, c.customer_name
ORDER BY total_order_value DESC
LIMIT 10;


-- =========================================================
-- 3. Month-wise order count for the last 12 months
--    "Last 12 months" relative to the most recent order_date in the data
--    (using MAX(order_date) instead of the real current date, since the
--    dataset is synthetic and 'now' has no meaning relative to it)
-- =========================================================
WITH latest_date AS (
    SELECT MAX(order_date) AS max_dt FROM orders
)
SELECT
    strftime('%Y-%m', o.order_date) AS year_month,
    COUNT(*) AS order_count
FROM orders o, latest_date l
WHERE o.order_date >= date(l.max_dt, '-12 months')
GROUP BY year_month
ORDER BY year_month;


-- =========================================================
-- 4. Customers who placed orders but never had any item delivered
-- =========================================================
SELECT DISTINCT o.customer_id, c.customer_name
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id IS NOT NULL
  AND o.customer_id NOT IN (
      SELECT customer_id FROM orders
      WHERE status = 'DELIVERED' AND customer_id IS NOT NULL
  );


-- =========================================================
-- 5. Products that were ordered but had more returns than purchases
--    (return = negative quantity row, purchase = positive quantity row)
-- =========================================================
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS total_purchased,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS total_returned
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
HAVING total_returned > total_purchased;


-- =========================================================
-- 6. Return rate (returned items / total items) per category
--    total items = purchased + returned (absolute unit count of activity)
-- =========================================================
SELECT
    p.category,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_units,
    SUM(ABS(oi.quantity)) AS total_units,
    ROUND(
        1.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0),
        4
    ) AS return_rate
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate DESC;
