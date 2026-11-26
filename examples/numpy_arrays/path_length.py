"""Total length of a GPS-like track, using NumPy's own functions as pipe steps."""

from functools import partial

import numpy as np

from paipu import Pipe, splat

TRACK = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0], [6.0, 11.0], [10.0, 14.0]])

steps = Pipe(partial(np.diff, axis=0))  # displacement between consecutive points
columns = Pipe(np.transpose)  # (n, 2) -> (2, n): all dx, then all dy


def without_pipes() -> float:
    return float(np.sum(np.hypot(*np.transpose(np.diff(TRACK, axis=0)))))


def with_pipes() -> float:
    return TRACK | steps | columns | splat(np.hypot) | Pipe(np.sum) | Pipe(float)


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print("track length:", with_pipes())
