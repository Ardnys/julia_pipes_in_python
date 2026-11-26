"""Month-over-month revenue growth, with a cleaning pipeline defined once and reused."""

from paipu import Pipe, broadcast, splat

from .steps import add_revenue, drop_cancelled, orders_frame, parse_dates, total_revenue

JANUARY = orders_frame([
    ("2026-01-03", "north", 3, 19.99, "shipped"),
    ("2026-01-04", "south", 10, 4.50, "shipped"),
    ("2026-01-05", "east", 2, 99.00, "cancelled"),
])
FEBRUARY = orders_frame([
    ("2026-02-02", "north", 5, 19.99, "shipped"),
    ("2026-02-03", "east", 2, 99.00, "shipped"),
    ("2026-02-08", "south", 6, 4.50, "cancelled"),
])


def growth(before: float, after: float) -> float:
    return (after - before) / before


@Pipe
def as_percent(x: float) -> str:
    return f"{x:+.1%}"


# Without pipes, "the cleaning" exists only as a nesting pattern you repeat at every call site.
def without_pipes() -> str:
    jan_total = total_revenue(add_revenue(parse_dates(drop_cancelled(JANUARY))))
    feb_total = total_revenue(add_revenue(parse_dates(drop_cancelled(FEBRUARY))))
    return as_percent(growth(jan_total, feb_total))


# With pipes, it is a value: name it, reuse it, extend it.
clean = drop_cancelled | parse_dates | add_revenue


def with_pipes() -> str:
    return [JANUARY, FEBRUARY] | broadcast(clean | total_revenue) | splat(growth) | as_percent


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print("revenue growth:", with_pipes())
