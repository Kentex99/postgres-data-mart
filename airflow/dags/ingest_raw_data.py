from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import csv

# -------------------------------------------------------------------
# DAG defaults
# -------------------------------------------------------------------
DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
RAW_DIR = '/opt/airflow/data/raw'

SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS raw;"

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.raw_sales (
    id           INTEGER PRIMARY KEY,
    product_id   INTEGER,
    customer_id  INTEGER,
    quantity     INTEGER,
    price        NUMERIC,
    sale_date    DATE
);
"""

# -------------------------------------------------------------------
# Task function
# -------------------------------------------------------------------
def ingest_sales():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_conn()
    cursor = conn.cursor()

    # Ensure schema & table exist
    cursor.execute(SCHEMA_SQL)
    cursor.execute(TABLE_SQL)
    conn.commit()  # commit DDL before inserts

    # Load CSV and insert rows
    with open(f"{RAW_DIR}/sales.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                """
                INSERT INTO raw.raw_sales
                (id, product_id, customer_id, quantity, price, sale_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    int(row['id']),
                    int(row['product_id']),
                    int(row['customer_id']),
                    int(row['quantity']),
                    float(row['price']),
                    row['sale_date']
                )
            )
    conn.commit()
    cursor.close()
    conn.close()

# -------------------------------------------------------------------
# DAG definition
# -------------------------------------------------------------------
with DAG(
    'ingest_raw_data',
    default_args=DEFAULT_ARGS,
    schedule_interval='@daily',
    catchup=False,
    tags=['raw'],
) as dag:

    task_ingest_sales = PythonOperator(
        task_id='ingest_sales',
        python_callable=ingest_sales,
    )
