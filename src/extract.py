"""Genera un dataset de pedidos de ejemplo (con datos sucios a propósito)."""
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")


def generate_orders(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")

    df = pd.DataFrame({
        "order_id": np.arange(1, n + 1),
        "order_date": dates.strftime("%Y-%m-%d"),
        "customer_id": rng.integers(1, 800, n),
        "country": rng.choice(
            ["Mexico", "mexico", "MEXICO", "Colombia", "Chile", "Peru", None],
            n, p=[0.30, 0.08, 0.04, 0.20, 0.15, 0.13, 0.10],
        ),
        "category": rng.choice(["Electronica", "Hogar", "Ropa", "Deportes"], n),
        "quantity": rng.integers(1, 10, n),
        "unit_price": np.round(rng.uniform(5, 500, n), 2),
    })

    # Datos sucios a propósito
    df.loc[rng.choice(n, 20, replace=False), "quantity"] = -1
    df.loc[rng.choice(n, 30, replace=False), "unit_price"] = np.nan
    df = pd.concat([df, df.sample(50, random_state=seed)], ignore_index=True)
    return df


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_orders()
    df.to_csv(RAW_DIR / "orders_raw.csv", index=False)
    print(f"Archivo crudo generado con {len(df)} filas")


if __name__ == "__main__":
    main()