# pandas examples

```sh
uv run --group examples python -m examples.pandas_frames.sales_report
uv run --group examples python -m examples.pandas_frames.monthly_growth
```

Both examples share the ordinary DataFrame-in, something-out functions in
[`steps.py`](steps.py): `drop_cancelled`, `parse_dates`, `add_revenue`, `revenue_by_region`,
`total_revenue` and `top_entry`, each decorated with `@Pipe`.

`paipu` sets `__pandas_priority__` on `Pipe`, so `frame | pipe` reaches the pipe instead of
pandas trying an element-wise "or".

## Sales report ([`sales_report.py`](sales_report.py))

Orders → drop cancelled → parse dates → add revenue → revenue per region → the best region →
`"Top region: east ($210.00)"`.
Types change along the way: `DataFrame` → `Series` → `tuple` → `str`.

### Without pipes: unreadable

```python
headline(*top_entry(revenue_by_region(add_revenue(parse_dates(drop_cancelled(ORDERS))))))
```

### "But pandas has `.pipe()`"

It does, and it is great right up to the moment the result stops being a DataFrame or Series:

```python
headline(
    *ORDERS.pipe(drop_cancelled)
    .pipe(parse_dates)
    .pipe(add_revenue)
    .pipe(revenue_by_region)
    .pipe(top_entry)
)
```

`top_entry` returns a plain `tuple`, which has no `.pipe()`, so the last step has to wrap the
whole chain from the outside again.

### With paipu™: beautiful

```python
(
    ORDERS
    | drop_cancelled
    | parse_dates
    | add_revenue
    | revenue_by_region
    | top_entry
    | splat(headline)
)
```

The pipe doesn't care what type flows through it, and `splat` passes the `(region, revenue)`
tuple to `headline(region, revenue)` without a `*` hidden at the front.

## Monthly growth ([`monthly_growth.py`](monthly_growth.py))

Clean two months of orders the same way, total each one, and compute the growth: `"+183.8%"`.

### Without pipes: unreadable

```python
jan_total = total_revenue(add_revenue(parse_dates(drop_cancelled(JANUARY))))
feb_total = total_revenue(add_revenue(parse_dates(drop_cancelled(FEBRUARY))))
as_percent(growth(jan_total, feb_total))
```

"The cleaning" isn't anything you can point to. It is a nesting pattern copied to every call
site, and changing it means changing it everywhere.

### With paipu™: beautiful

```python
clean = drop_cancelled | parse_dates | add_revenue

[JANUARY, FEBRUARY] | broadcast(clean | total_revenue) | splat(growth) | as_percent
```

The cleaning pipeline is a value: name it once, reuse it, extend it (`clean | total_revenue`).
`broadcast` applies it to both months, and `splat` passes the two totals to `growth(before, after)`.

> Note: type checkers infer `frame | pipe` as a `DataFrame`, because pandas-stubs declare
> `DataFrame.__or__` as accepting anything. At runtime the pipe runs correctly. `Series | pipe`
> and `Index | pipe` are typed correctly.

> Note: `orders |= clean` does **not** work on DataFrames, because pandas' own in-place `|`
> runs first. Write `orders = orders | clean`.
