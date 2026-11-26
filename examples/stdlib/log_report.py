"""Summarise which services are failing, from raw log lines."""

from collections import Counter
from typing import NamedTuple

from paipu import Pipe, broadcast

LOG = """\
2026-11-22T10:00:01 INFO  auth      user logged in
2026-11-22T10:00:03 ERROR payments  card declined
2026-11-22T10:00:04 ERROR payments  gateway timeout
2026-11-22T10:00:09 WARN  search    slow query
2026-11-22T10:00:12 ERROR auth      token expired
2026-11-22T10:00:15 ERROR payments  gateway timeout
"""


class Entry(NamedTuple):
    timestamp: str
    level: str
    service: str
    message: str


lines = Pipe(str.splitlines)


@broadcast
def parse(line: str) -> Entry:
    timestamp, level, service, message = line.split(maxsplit=3)
    return Entry(timestamp, level, service, message)


@Pipe
def errors_only(entries: list[Entry]) -> list[Entry]:
    return [e for e in entries if e.level == "ERROR"]


@Pipe
def count_by_service(entries: list[Entry]) -> Counter[str]:
    return Counter(e.service for e in entries)


@Pipe
def format_report(counts: Counter[str]) -> str:
    return "\n".join(f"{service:<10} {n} error(s)" for service, n in counts.most_common())


def without_pipes() -> str:
    return format_report(count_by_service(errors_only(parse(lines(LOG)))))


def with_pipes() -> str:
    return LOG | lines | parse | errors_only | count_by_service | format_report


if __name__ == "__main__":
    assert without_pipes() == with_pipes()
    print(with_pipes())
