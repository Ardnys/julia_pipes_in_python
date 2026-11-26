"""Ordinary DataFrame-in, something-out functions, shared by the pandas examples."""

import pandas as pd

from paipu import Pipe


@Pipe
def drop_cancelled(orders: pd.DataFrame) -> pd.DataFrame:
    return orders[orders["status"] != "cancelled"]


@Pipe
def parse_dates(orders: pd.DataFrame) -> pd.DataFrame:
    return orders.assign(date=pd.to_datetime(orders["date"]))


@Pipe
def add_revenue(orders: pd.DataFrame) -> pd.DataFrame:
    return orders.assign(revenue=orders["units"] * orders["unit_price"])


@Pipe
def revenue_by_region(orders: pd.DataFrame) -> pd.Series:
    return orders.groupby("region")["revenue"].sum().sort_values(ascending=False)


@Pipe
def total_revenue(orders: pd.DataFrame) -> float:
    return float(orders["revenue"].sum())


@Pipe
def top_entry(series: pd.Series) -> tuple[str, float]:
    return str(series.index[0]), float(series.iloc[0])


def orders_frame(rows: list[tuple[str, str, int, float, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["date", "region", "units", "unit_price", "status"])
