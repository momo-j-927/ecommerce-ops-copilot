import csv
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORDERS_CSV = PROJECT_ROOT / "data" / "orders.csv"
DB_PATH = PROJECT_ROOT / "runtime" / "ops.db"


def initialize_database() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                region TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                amount REAL NOT NULL,
                discount_rate REAL NOT NULL,
                refund_flag INTEGER NOT NULL,
                delivery_days INTEGER NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if count == 0:
            with ORDERS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            conn.executemany(
                """
                INSERT INTO orders VALUES (
                    :order_id, :order_date, :region, :channel, :status,
                    :amount, :discount_rate, :refund_flag, :delivery_days
                )
                """,
                rows,
            )
    return DB_PATH


def get_sales_summary(region: str | None = None) -> dict[str, Any]:
    initialize_database()
    where = "WHERE region = ?" if region else ""
    params = (region,) if region else ()
    query = f"""
        SELECT COUNT(*) AS order_count,
               ROUND(SUM(amount), 2) AS revenue,
               ROUND(AVG(amount), 2) AS average_order_value,
               ROUND(AVG(refund_flag) * 100, 2) AS refund_rate
        FROM orders
        {where}
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(query, params).fetchone()
    return {
        "region": region or "全部地区",
        "order_count": row["order_count"],
        "revenue": row["revenue"],
        "average_order_value": row["average_order_value"],
        "refund_rate_percent": row["refund_rate"],
    }


def detect_order_anomalies() -> list[dict[str, Any]]:
    initialize_database()
    query = """
        SELECT order_id, order_date, region, amount, discount_rate,
               refund_flag, delivery_days,
               CASE
                   WHEN amount <= 0 THEN 'zero_amount'
                   WHEN discount_rate >= 0.60 THEN 'high_discount'
                   WHEN delivery_days >= 10 THEN 'delivery_delay'
                   WHEN refund_flag = 1 THEN 'refund'
               END AS anomaly_type
        FROM orders
        WHERE amount <= 0
           OR discount_rate >= 0.60
           OR delivery_days >= 10
           OR refund_flag = 1
        ORDER BY order_date, order_id
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]
