{{ config(materialized = 'table') }}

SELECT
    customer_id            AS customer_key
FROM {{ ref('stg_raw_sales') }}
GROUP BY customer_id
