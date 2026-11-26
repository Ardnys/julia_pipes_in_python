"""Which region made the most money? DataFrame -> DataFrame -> Series -> tuple -> str."""

from paipu import splat

from .steps import add_revenue, drop_cancelled, orders_frame, parse_dates, revenue_by_region, top_entry

ORDERS = orders_frame([
    ("2026-01-03", "north", 3, 19.99, "shipped"),
    ("2026-01-04", "south", 10, 4.50, "shipped"),
    ("2026-01-04", "north", 1, 249.00, "cancelled"),
    ("2026-01-05", "east", 2, 99.00, "shipped"),
    ("2026-01-07", "south", 4, 19.99, "pending"),
    ("2026-01-09", "east", 1, 12.00, "shipped"),
])


def headline(region: str, revenue: float) -> str:
    return f"Top region: {region} (${revenue:,.2f})"


def without_pipes() -> str:
    return headline(*top_entry(revenue_by_region(add_revenue(parse_dates(drop_cancelled(ORDERS))))))


def with_pandas_pipe_method() -> str:
    # pandas' own .pipe() chains nicely, but only while the result is a DataFrame or Series.
    return headline(
        *ORDERS.pipe(drop_cancelled)
        .pipe(parse_dates)
        .pipe(add_revenue)
        .pipe(revenue_by_region)
        .pipe(top_entry)
    )


def with_pipes() -> str:
    # pandas-stubs type `DataFrame | anything` as DataFrame, so type checkers miss that
    # `Pipe.__ror__` handles it at runtime. Series and Index are typed correctly.
    return (  # pyright: ignore[reportReturnType]
        ORDERS
        | drop_cancelled
        | parse_dates
        | add_revenue
        | revenue_by_region
        | top_entry
        | splat(headline)
    )


if __name__ == "__main__":
    assert without_pipes() == with_pandas_pipe_method() == with_pipes()
    print(with_pipes())
