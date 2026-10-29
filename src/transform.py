"""Limpia los pedidos crudos y los guarda en Parquet particionado por mes."""
import shutil
from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw/orders_raw.csv")
OUT_DIR = Path("data/processed/orders")


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="order_id").copy()
    df["country"] = df["country"].str.strip().str.title().fillna("Desconocido")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date", "unit_price"])
    df = df[df["quantity"] > 0].copy()
    df["total"] = (df["quantity"] * df["unit_price"]).round(2)
    df["year_month"] = df["order_date"].dt.strftime("%Y-%m")
    df["order_date"] = df["order_date"].dt.date
    return df


def main() -> None:
    raw = pd.read_csv(RAW_FILE)
    clean = clean_orders(raw)

    print(f"Filas originales : {len(raw)}")
    print(f"Filas limpias    : {len(clean)}")
    print(f"Filas descartadas: {len(raw) - len(clean)}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    clean.to_parquet(OUT_DIR, partition_cols=["year_month"], index=False)
    print(f"Parquet guardado en {OUT_DIR}")


if __name__ == "__main__":
    main()