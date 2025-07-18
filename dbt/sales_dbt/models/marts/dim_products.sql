{{ config(materialized = 'table') }}

SELECT
    product_id            AS product_key,
    MAX(price)            AS current_price
FROM {{ ref('stg_raw_sales') }}
GROUP BY product_id
