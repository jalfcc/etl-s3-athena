"""Crea la base y la tabla en Athena y consulta con SQL los Parquet en S3."""
import os
import time

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.environ["BUCKET_NAME"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
DATABASE = "etl_demo"
OUTPUT = f"s3://{BUCKET}/athena-results/"

athena = boto3.client("athena", region_name=REGION)


def run_query(sql: str, database: str | None = None) -> pd.DataFrame:
    params = {"QueryString": sql, "ResultConfiguration": {"OutputLocation": OUTPUT}}
    if database:
        params["QueryExecutionContext"] = {"Database": database}
    query_id = athena.start_query_execution(**params)["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)["QueryExecution"]["Status"]
        if status["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if status["State"] != "SUCCEEDED":
        raise RuntimeError(f"{status['State']}: {status.get('StateChangeReason', '')}")

    if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
        return pd.DataFrame()  # DDL: no devuelve filas

    rows = athena.get_query_results(QueryExecutionId=query_id)["ResultSet"]["Rows"]
    header = [c["VarCharValue"] for c in rows[0]["Data"]]
    data = [[c.get("VarCharValue") for c in r["Data"]] for r in rows[1:]]
    return pd.DataFrame(data, columns=header)


def main() -> None:
    run_query(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

    run_query(f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS orders (
            order_id bigint,
            order_date date,
            customer_id bigint,
            country string,
            category string,
            quantity bigint,
            unit_price double,
            total double
        )
        PARTITIONED BY (year_month string)
        STORED AS PARQUET
        LOCATION 's3://{BUCKET}/orders/'
    """, DATABASE)
    run_query("MSCK REPAIR TABLE orders", DATABASE)  # registra las particiones por mes

    print("\nVentas por país:")
    print(run_query("""
        SELECT country, COUNT(*) AS pedidos, ROUND(SUM(total), 2) AS ventas
        FROM orders
        GROUP BY country
        ORDER BY ventas DESC
    """, DATABASE))

    print("\nVentas por categoría en enero y febrero 2025:")
    print(run_query("""
        SELECT year_month, category, ROUND(SUM(total), 2) AS ventas
        FROM orders
        WHERE year_month IN ('2025-01', '2025-02')
        GROUP BY year_month, category
        ORDER BY year_month, ventas DESC
    """, DATABASE))


if __name__ == "__main__":
    main()