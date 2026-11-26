"""Find when a drifting, noisy sensor signal peaks."""

import numpy as np

from paipu import Pipe

rng = np.random.default_rng(seed=0)
T = np.linspace(0, 10, 500)
RAW = 0.3 * T + np.sin(2 * np.pi * 0.4 * T) + rng.normal(0, 0.2, T.size)  # drift + signal + noise


@Pipe
def detrend(x: np.ndarray) -> np.ndarray:
    idx = np.arange(x.size)
    return x - np.polyval(np.polyfit(idx, x, deg=1), idx)


@Pipe
def zscore(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / x.std()


@Pipe
def smooth(x: np.ndarray, window: int = 25) -> np.ndarray:
    return np.convolve(x, np.ones(window) / window, mode="same")


@Pipe
def peak_indices(x: np.ndarray, threshold: float = 1.0) -> np.ndarray:
    """The highest point of each stretch where the signal is above `threshold`."""
    above = x > threshold
    stretches = np.split(np.arange(x.size), np.flatnonzero(np.diff(above)) + 1)
    return np.array([s[np.argmax(x[s])] for s in stretches if above[s[0]]])


def without_pipes() -> np.ndarray:
    return T.take(peak_indices(smooth(zscore(detrend(RAW)))))


def with_pipes() -> np.ndarray:
    return RAW | detrend | zscore | smooth | peak_indices | Pipe(T.take)


if __name__ == "__main__":
    assert np.array_equal(without_pipes(), with_pipes())
    print("peaks at t =", with_pipes().round(2))
