"""How much of a noisy grayscale image is bright?"""

import numpy as np

from paipu import Pipe

rng = np.random.default_rng(seed=1)
yy, xx = np.mgrid[0:64, 0:64]
IMAGE = (
    255 * np.exp(-((xx - 40) ** 2 + (yy - 24) ** 2) / 120)  # a bright blob
    + rng.normal(0, 25, (64, 64))  # sensor noise
    + 40  # dark offset
)


@Pipe
def crop_border(img: np.ndarray) -> np.ndarray:
    return img[4:-4, 4:-4]


@Pipe
def normalize(img: np.ndarray) -> np.ndarray:
    return (img - img.min()) / np.ptp(img)


@Pipe
def box_blur(img: np.ndarray) -> np.ndarray:
    padded = np.pad(img, 1, mode="edge")
    h, w = img.shape
    return np.mean([padded[dy : dy + h, dx : dx + w] for dy in range(3) for dx in range(3)], axis=0)


@Pipe
def bright_mask(img: np.ndarray) -> np.ndarray:
    return img > 0.5


@Pipe
def fraction(mask: np.ndarray) -> float:
    return float(mask.mean())


@Pipe
def as_percent(x: float) -> str:
    return f"{x:.1%}"


def without_pipes() -> str:
    return as_percent(fraction(bright_mask(box_blur(normalize(crop_border(IMAGE))))))


def with_pipes() -> str:
    return IMAGE | crop_border | normalize | box_blur | bright_mask | fraction | as_percent


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print("bright area:", with_pipes())
