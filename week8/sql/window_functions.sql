-- window_functions.sql
-- Advanced Queries (7-16): Window Functions, CTEs, Subqueries

-- =========================================================
-- 7. Running total of revenue per region, ordered by date
-- =========================================================
WITH daily AS (
    SELECT
        o.region_code,
        date(o.order_date) AS order_date,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY o.region_code, date(o.order_date)
)
SELECT
    region_code,
    order_date,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(SUM(daily_revenue) OVER (
        PARTITION BY region_code ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total
FROM daily
ORDER BY region_code, order_date;


-- =========================================================
-- 8. Rank products by total revenue within each category (DENSE_RANK)
--    Products with the same revenue get the same rank (that's exactly
--    what DENSE_RANK does, vs RANK which would leave gaps).
-- =========================================================
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    total_revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;


-- =========================================================
-- 9. Days between consecutive orders per customer (LAG), flag "At Risk"
-- =========================================================
WITH customer_orders AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        previous_order_date,
        CASE
            WHEN previous_order_date IS NOT NULL
            THEN julianday(order_date) - julianday(previous_order_date)
        END AS days_gap
    FROM customer_orders
),
avg_gap AS (
    SELECT customer_id, AVG(days_gap) AS avg_days_gap
    FROM gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT
    g.customer_id,
    g.order_date,
    g.previous_order_date,
    ROUND(g.days_gap, 2) AS days_gap,
    CASE WHEN a.avg_days_gap > 30 THEN 'At Risk' ELSE 'Active' END AS risk_flag
FROM gaps g
LEFT JOIN avg_gap a ON a.customer_id = g.customer_id
ORDER BY g.customer_id, g.order_date;


-- =========================================================
-- 10. CTE with multiple levels: monthly revenue per customer -> tier -> counts per month
-- =========================================================
WITH monthly_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monthly_rev
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id, year_month
),
tiered AS (
    SELECT
        customer_id,
        year_month,
        monthly_rev,
        CASE
            WHEN monthly_rev > 10000 THEN 'High'
            WHEN monthly_rev >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS tier
    FROM monthly_revenue
)
SELECT
    year_month,
    tier,
    COUNT(*) AS customer_count
FROM tiered
GROUP BY year_month, tier
ORDER BY year_month, tier;


-- =========================================================
-- 11. NTILE: divide customers into 4 quartiles by lifetime value
-- =========================================================
WITH lifetime_value AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_value, 2) AS total_value,
    NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS quartile_label
FROM lifetime_value
ORDER BY quartile, total_value DESC;


-- =========================================================
-- 12. Year-over-year comparison: each month's revenue vs same month last year
-- =========================================================
WITH monthly_rev AS (
    SELECT
        CAST(strftime('%Y', o.order_date) AS INTEGER) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY year, month
)
SELECT
    curr.year,
    curr.month,
    ROUND(curr.revenue, 2) AS revenue,
    ROUND(prev.revenue, 2) AS prev_year_revenue,
    CASE
        WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
        ELSE ROUND((curr.revenue - prev.revenue) / prev.revenue * 100, 2)
    END AS yoy_growth_percent
FROM monthly_rev curr
LEFT JOIN monthly_rev prev
    ON prev.year = curr.year - 1 AND prev.month = curr.month
ORDER BY curr.year, curr.month;


-- =========================================================
-- 13. First/last purchased category per customer, flag category_shift
-- =========================================================
WITH customer_category_orders AS (
    SELECT
        o.customer_id,
        o.order_date,
        p.category,
        FIRST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_category,
        LAST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_category
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id IS NOT NULL
)
SELECT DISTINCT
    customer_id,
    first_category,
    last_category,
    CASE WHEN first_category != last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM customer_category_orders
ORDER BY customer_id;


-- =========================================================
-- 14. Cumulative distribution: % of total revenue from top N% of customers
-- =========================================================
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue,
        SUM(revenue) OVER () AS grand_total
    FROM customer_revenue
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(cumulative_revenue / grand_total * 100, 2) AS cumulative_percent
FROM ranked
ORDER BY revenue DESC;


-- =========================================================
-- 15. Cohort analysis: registration month cohorts, retention by month 0-3
-- =========================================================
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
customer_order_months AS (
    SELECT DISTINCT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month
    FROM orders o
    WHERE o.customer_id IS NOT NULL
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        c.customer_id,
        com.order_month,
        -- month index = number of whole months between cohort month and order month
        (CAST(strftime('%Y', om_date.d) AS INTEGER) - CAST(strftime('%Y', cm_date.d) AS INTEGER)) * 12
        + (CAST(strftime('%m', om_date.d) AS INTEGER) - CAST(strftime('%m', cm_date.d) AS INTEGER)) AS month_index
    FROM cohorts c
    JOIN customer_order_months com ON com.customer_id = c.customer_id
    JOIN (SELECT c.customer_id, c.cohort_month || '-01' AS d FROM cohorts c) cm_date ON cm_date.customer_id = c.customer_id
    JOIN (SELECT com.customer_id, com.order_month, com.order_month || '-01' AS d
          FROM customer_order_months com) om_date
        ON om_date.customer_id = c.customer_id AND om_date.order_month = com.order_month
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.month_index,
    COUNT(DISTINCT ca.customer_id) AS customers_active,
    ROUND(100.0 * COUNT(DISTINCT ca.customer_id) / cs.cohort_size, 2) AS retention_rate_percent
FROM cohort_activity ca
JOIN cohort_sizes cs ON cs.cohort_month = ca.cohort_month
WHERE ca.month_index BETWEEN 0 AND 3
GROUP BY ca.cohort_month, ca.month_index
ORDER BY ca.cohort_month, ca.month_index;


-- =========================================================
-- 16. Products frequently bought together (self-join, dedup A-B/B-A)
-- =========================================================
SELECT
    p1.product_name AS product_a,
    p2.product_name AS product_b,
    COUNT(*) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.product_id < oi2.product_id   -- ensures each pair counted once, A-B not B-A too
JOIN products p1 ON p1.product_id = oi1.product_id
JOIN products p2 ON p2.product_id = oi2.product_id
GROUP BY p1.product_id, p2.product_id
ORDER BY times_bought_together DESC
LIMIT 20;
