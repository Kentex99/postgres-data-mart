{{ config(materialized = 'table') }}

WITH sales AS (
    SELECT *
    FROM {{ ref('stg_raw_sales') }}
)

SELECT
    s.id                        AS sales_key,
    c.customer_key,
    p.product_key,
    s.quantity,
    s.price,
    s.sale_date,
    s.quantity * s.price        AS gross_amount
FROM sales           AS s
LEFT JOIN {{ ref('dim_customers') }} AS c
       ON c.customer_key = s.customer_id
LEFT JOIN {{ ref('dim_products') }}  AS p
       ON p.product_key   = s.product_id
