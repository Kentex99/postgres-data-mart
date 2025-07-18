-- models/staging/stg_raw_sales.sql

{{ config(materialized = 'view') }}

SELECT
    id,
    product_id,
    customer_id,
    quantity,
    price,
    sale_date
FROM raw.raw_sales
