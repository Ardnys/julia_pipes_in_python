"""The most common words in a text."""

import re
from collections import Counter

from paipu import Pipe

TEXT = """
It was the best of times, it was the worst of times, it was the age of wisdom,
it was the age of foolishness, it was the epoch of belief, it was the epoch of
incredulity, it was the season of light, it was the season of darkness.
"""

STOPWORDS = frozenset({"it", "was", "the", "of", "a", "and"})


@Pipe
def lowercase(text: str) -> str:
    return text.lower()


@Pipe
def words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text)


@Pipe
def drop_stopwords(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS]


@Pipe
def count(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


@Pipe
def top_three(counts: Counter[str]) -> list[tuple[str, int]]:
    return counts.most_common(3)


def without_pipes() -> list[tuple[str, int]]:
    return top_three(count(drop_stopwords(words(lowercase(TEXT)))))


def with_pipes() -> list[tuple[str, int]]:
    return TEXT | lowercase | words | drop_stopwords | count | top_three


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print(with_pipes())
