from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import csv, os

# ------------------------------------------------------------------------
# DAG definition
# ------------------------------------------------------------------------
with DAG(
    dag_id="ingest_raw_sales_v2",
    start_date=datetime(2025, 7, 1),
    schedule_interval=None,     # manual trigger only
    catchup=False,
    tags=["demo"],
) as dag:

    # 1) create schema & table once
    create_table = PostgresOperator(
        task_id="create_raw_table",
        postgres_conn_id="postgres_default",
        sql="""
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE TABLE IF NOT EXISTS raw.raw_sales (
            id           INTEGER PRIMARY KEY,
            product_id   INTEGER,
            customer_id  INTEGER,
            quantity     INTEGER,
            price        NUMERIC,
            sale_date    DATE
        );
        """,
    )

    # 2) simple loader
    def load_csv_to_postgres():
        csv_path = "/opt/airflow/data/raw/sales.csv"
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"{csv_path} not found.")

        hook = PostgresHook(postgres_conn_id="postgres_default")
        conn = hook.get_conn()
        cur = conn.cursor()

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = [
                (
                    int(r["id"]),
                    int(r["product_id"]),
                    int(r["customer_id"]),
                    int(r["quantity"]),
                    float(r["price"]),
                    r["sale_date"],
                )
                for r in reader
            ]

        insert_sql = """
            INSERT INTO raw.raw_sales
            (id, product_id, customer_id, quantity, price, sale_date)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """
        hook.insert_rows("raw.raw_sales", rows, commit_every=1000)
        conn.commit()
        cur.close()
        conn.close()

    load_data = PythonOperator(
        task_id="load_sales_csv",
        python_callable=load_csv_to_postgres,
    )

    create_table >> load_data
