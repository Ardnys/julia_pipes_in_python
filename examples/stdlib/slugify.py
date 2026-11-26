"""Turn blog post titles into URL slugs."""

import re
import unicodedata

from paipu import Pipe, broadcast

TITLES = [
    "Crème Brûlée: A Love Story!",
    "Why I    Stopped Using Tabs (Sort Of)",
    "Ünïcödé is Fun & Easy?",
]


def slugify_without_pipes(title: str) -> str:
    return "-".join(
        re.sub(
            r"[^\w\s-]",
            "",
            unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii"),
        )
        .lower()
        .split()
    )


@Pipe
def strip_accents(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


@Pipe
def drop_punctuation(text: str) -> str:
    return re.sub(r"[^\w\s-]", "", text)


slugify = strip_accents | drop_punctuation | str.lower | str.split | "-".join


def without_pipes() -> list[str]:
    return [slugify_without_pipes(title) for title in TITLES]


def with_pipes() -> list[str]:
    return TITLES | broadcast(slugify)


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print(with_pipes())
