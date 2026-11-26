# paipu™ examples

Nested function calls read **inside-out**: the first step is buried in the middle and the
last step comes first. Pipes read the way the data flows: **left to right**, one step per `|`.

| Directory | What's inside |
| --- | --- |
| [`stdlib/`](stdlib/) | Text processing, log summaries, slugs: plain Python, no dependencies |
| [`numpy_arrays/`](numpy_arrays/) | Signal cleanup, image thresholding, wrapping NumPy's own functions |
| [`pandas_frames/`](pandas_frames/) | DataFrame-in, something-out functions chained into reports |

Every example computes its result both ways, asserts they match, and prints it.

## Running

From the repository root (the examples import `paipu` from there):

```sh
uv run python -m examples.stdlib.word_frequency
uv run --group examples python -m examples.numpy_arrays.sensor_peaks
uv run --group examples python -m examples.pandas_frames.sales_report
```

The `examples` dependency group in `pyproject.toml` provides NumPy and pandas.

## Two things to keep in mind

1. **The step right after the data must be a `Pipe`.** `x | f | str.upper` fails, because the
   second `|` sees two plain objects. Use `x | f | Pipe(str.upper)`, or compose first:
   `x | (f | str.upper)`. Composing a `Pipe` with any plain callable works anywhere:
   `strip_accents | str.lower | "-".join`.
2. **`|=` does not work on dicts, NumPy arrays or pandas objects.** Their own in-place `|`
   runs first. Write `frame = frame | clean` instead of `frame |= clean`.
