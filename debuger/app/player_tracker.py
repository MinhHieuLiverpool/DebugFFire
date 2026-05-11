import os
import re
import time
from typing import Iterator

INIT_TRACKING_PATTERN = re.compile(r"\[InitTrackingPlayer\]\s+\d+\s+->\s+(\S+)")
ADD_PLAYER_PATTERN = re.compile(
    r"\[UIModelSpectator\]\s+AddPlayer\s+id(\d+),name([^,\s]+)"
)


def follow_lines(path: str, poll_interval: float = 0.2) -> Iterator[str]:
    if poll_interval <= 0:
        poll_interval = 0.1

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                yield line.rstrip("\n")
            else:
                time.sleep(poll_interval)


def iter_player_names(path: str, poll_interval: float = 0.2) -> Iterator[str]:
    for line in follow_lines(path, poll_interval=poll_interval):
        match = INIT_TRACKING_PATTERN.search(line)
        if match:
            yield match.group(1)


def parse_add_player_line(line: str) -> tuple[int, str] | None:
    match = ADD_PLAYER_PATTERN.search(line)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def iter_add_player_events(path: str, poll_interval: float = 0.2) -> Iterator[tuple[int, str]]:
    for line in follow_lines(path, poll_interval=poll_interval):
        parsed = parse_add_player_line(line)
        if parsed:
            yield parsed
