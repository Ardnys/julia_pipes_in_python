# NumPy examples

```sh
uv run --group examples python -m examples.numpy_arrays.sensor_peaks
uv run --group examples python -m examples.numpy_arrays.bright_spots
uv run --group examples python -m examples.numpy_arrays.path_length
```

`paipu` sets `__array_ufunc__ = None` on `Pipe`, so `array | pipe` reaches the pipe instead
of NumPy trying an element-wise "or".

## Sensor peaks ([`sensor_peaks.py`](sensor_peaks.py))

A drifting, noisy sine wave: remove the drift, standardize, smooth, find the peaks, and convert
sample indices into times.

### Without pipes: unreadable

```python
T.take(peak_indices(smooth(zscore(detrend(RAW)))))
```

Where does the data come in? Count four parentheses from the right. And `T.take`, the last step,
is up front, looking like the main event.

### With paipu™: beautiful

```python
RAW | detrend | zscore | smooth | peak_indices | Pipe(T.take)
```

A signal-processing chain reads like the block diagram you would draw for it. Any bound
method, here `T.take`, becomes a step with `Pipe(...)`.

## Bright spots ([`bright_spots.py`](bright_spots.py))

A noisy grayscale image → crop → normalize → blur → threshold → fraction of bright pixels → `"10.0%"`.
Types change along the way: `ndarray[float]` → `ndarray[bool]` → `float` → `str`.

### Without pipes: unreadable

```python
as_percent(fraction(bright_mask(box_blur(normalize(crop_border(IMAGE))))))
```

### With paipu™: beautiful

```python
IMAGE | crop_border | normalize | box_blur | bright_mask | fraction | as_percent
```

Six steps, zero parentheses. To check intermediate results, cut the line anywhere:
`IMAGE | crop_border | normalize` is already a valid expression.

## Path length ([`path_length.py`](path_length.py))

The total length of a track of points, using NumPy's own functions as the steps.

### Without pipes: unreadable

```python
float(np.sum(np.hypot(*np.transpose(np.diff(TRACK, axis=0)))))
```

The `*` unpacking is easy to miss, and `axis=0` belongs to `np.diff`, five calls deep.

### With paipu™: beautiful

```python
steps = Pipe(partial(np.diff, axis=0))  # displacement between consecutive points
columns = Pipe(np.transpose)            # (n, 2) -> (2, n): all dx, then all dy

TRACK | steps | columns | splat(np.hypot) | Pipe(np.sum) | Pipe(float)
```

Parameters stay next to their function (inside `partial`), steps get names that say *what*
they do, and `splat(np.hypot)` makes the unpacking explicit: the two rows become `np.hypot(dx, dy)`.
