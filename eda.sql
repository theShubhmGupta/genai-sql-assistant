ATTACH DATABASE 'D:/Documents/Projects/Project - genai_sql_assistant/data/target.db' AS target;

-- 1. Import the dataset and do usual exploratory analysis steps like checking the structure & characteristics of the dataset:

-- 1.A - Data type of all columns in the “customers” table.
PRAGMA target.table_info(customers);

-- 1.B - Get the time range between which the orders were placed

SELECT
    MIN(order_purchase_timestamp) AS first_order_date,
    MAX(order_purchase_timestamp) AS last_order_date
FROM target.orders;

-- 1.C - Count the Cities & States of customers who ordered during the given period.

SELECT 
    COUNT(DISTINCT customer_city) AS total_cities,
    COUNT(DISTINCT customer_state) AS total_states
FROM target.customers;

-- 2. In-depth Exploration:

-- 2.A - Is there a growing trend in the no. of orders placed over the past years?

SELECT
    strftime('%Y', order_purchase_timestamp) AS order_year,
    count(*) as total_orders
FROM target.orders
GROUP BY order_year
ORDER BY order_year;

-- 2.B - Can we see some kind of monthly seasonality in terms of the no. of orders being placed?

SELECT
    strftime('%Y', order_purchase_timestamp) AS order_year,
    strftime('%m', order_purchase_timestamp) AS order_month,
    COUNT(*) AS total_orders
FROM target.orders
GROUP BY order_year,order_month
ORDER BY order_year,order_month;


-- 2.C - During what time of the day, do the Brazilian customers mostly place their orders? (Dawn, Morning, Afternoon or Night)
-- 0-6 hrs : Dawn
-- 7-12 hrs : Mornings
-- 13-18 hrs : Afternoon
-- 19-23 hrs : Night

SELECT
    CASE
        WHEN CAST(strftime('%H', order_purchase_timestamp) AS INTEGER) BETWEEN 0 AND 6
            THEN 'Dawn'
        WHEN CAST(strftime('%H', order_purchase_timestamp) AS INTEGER) BETWEEN 7 AND 12
            THEN 'Morning'
        WHEN CAST(strftime('%H', order_purchase_timestamp) AS INTEGER) BETWEEN 13 AND 18
            THEN 'Afternoon'
        ELSE 'Night'
    END AS time_of_day,
    COUNT(*) AS total_orders
FROM target.orders
GROUP BY time_of_day
ORDER BY total_orders DESC;


-- 3. Evolution of E-commerce orders in the Brazil region:

-- 3.A - Get the month-on-month no. of orders placed in each state.

SELECT
    c.customer_state,
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COUNT(o.order_id) AS total_orders
FROM target.orders o
JOIN target.customers c
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_state,
    order_month
ORDER BY
    c.customer_state,
    order_month;

-- 3.B - How are the customers distributed across all the states?

SELECT
    customer_state,
    COUNT(DISTINCT customer_id) AS total_customers
FROM target.customers
GROUP BY customer_state
ORDER BY total_customers DESC;

-- 4. Impact on Economy: Analyse the money movement by e-commerce by looking at order prices, freight and others.

-- 4.A - Get the % increase in the cost of orders from year 2017 to 2018 (include months between Jan to Aug only).

WITH yearly_payments AS (
    SELECT
        strftime('%Y', o.order_purchase_timestamp) AS year,
        SUM(p.payment_value) AS total_payment
    FROM target.orders o
    JOIN target.payments p
        ON o.order_id = p.order_id
    WHERE strftime('%m', o.order_purchase_timestamp) BETWEEN '01' AND '08'
      AND strftime('%Y', o.order_purchase_timestamp) IN ('2017', '2018')
    GROUP BY year
)
SELECT
    y2017.total_payment AS payment_2017,
    y2018.total_payment AS payment_2018,
    ROUND(
        ((y2018.total_payment - y2017.total_payment) * 100.0) 
        / y2017.total_payment,
        2
    ) AS percentage_increase
FROM yearly_payments y2017
JOIN yearly_payments y2018
    ON y2017.year = '2017'
   AND y2018.year = '2018';

-- 4.B - Calculate the Total & Average value of order price for each state.

SELECT
    c.customer_state,
    ROUND(SUM(oi.price), 2) AS total_order_value,
    ROUND(AVG(oi.price), 2) AS avg_order_value
FROM target.order_items oi
JOIN target.orders o
    ON oi.order_id = o.order_id
JOIN target.customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY total_order_value DESC;

-- 4.C - Calculate the Total & Average value of order freight for each state.

SELECT
    c.customer_state,
    ROUND(SUM(oi.freight_value), 2) AS total_freight_value,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight_value
FROM target.order_items oi
JOIN target.orders o
    ON oi.order_id = o.order_id
JOIN target.customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY total_freight_value DESC;

-- 5. Analysis based on sales, freight and delivery time.

-- 5.A — Delivery time & estimated vs actual delivery difference

SELECT
    order_id,

    -- Actual delivery time in days
    ROUND(
        JULIANDAY(order_delivered_customer_date) -
        JULIANDAY(order_purchase_timestamp),
        2
    ) AS time_to_deliver_days,

    -- Difference between estimated & actual delivery (in days)
    ROUND(
        JULIANDAY(order_estimated_delivery_date) -
        JULIANDAY(order_delivered_customer_date),
        2
    ) AS diff_estimated_delivery_days

FROM target.orders
WHERE order_delivered_customer_date IS NOT NULL;


-- 5.B — Top 5 states with highest & lowest average freight value

SELECT
    c.customer_state,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight
FROM target.order_items oi
JOIN target.orders o ON oi.order_id = o.order_id
JOIN target.customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY avg_freight DESC
LIMIT 5;

SELECT
    c.customer_state,
    ROUND(AVG(oi.freight_value), 2) AS avg_freight
FROM target.order_items oi
JOIN target.orders o ON oi.order_id = o.order_id
JOIN target.customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY avg_freight ASC
LIMIT 5;


-- 5.C - Top 5 states with highest & lowest average delivery time

SELECT
    c.customer_state,
    ROUND(
        AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_purchase_timestamp)
        ),
        2
    ) AS avg_delivery_days
FROM target.orders o
JOIN target.customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC
LIMIT 5;


SELECT
    c.customer_state,
    ROUND(
        AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_purchase_timestamp)
        ),
        2
    ) AS avg_delivery_days
FROM target.orders o
JOIN target.customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days ASC
LIMIT 5;


-- 5.D - States where delivery is faster than estimated

SELECT
    c.customer_state,
    ROUND(
        AVG(
            JULIANDAY(o.order_estimated_delivery_date) -
            JULIANDAY(o.order_delivered_customer_date)
        ),
        2
    ) AS avg_days_early
FROM target.orders o
JOIN target.customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_days_early DESC
LIMIT 5;

-- 6. Analysis based on the payments:

-- 6.A — Month-on-month number of orders by payment type

SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    p.payment_type,
    COUNT(DISTINCT o.order_id) AS total_orders
FROM target.orders o
JOIN target.payments p
    ON o.order_id = p.order_id
GROUP BY
    order_month,
    p.payment_type
ORDER BY
    order_month,
    total_orders DESC;

-- 6.B - Number of orders based on payment installments

SELECT
    payment_installments,
    COUNT(DISTINCT order_id) AS total_orders
FROM target.payments
GROUP BY payment_installments
ORDER BY payment_installments;
