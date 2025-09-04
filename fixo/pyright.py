import dataclasses as dc
import json

from pathlib import Path
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Iterator, TypeAlias


File: TypeAlias = str | Path | TextIOWrapper


@dc.dataclass
class LineCharacter:
    line: int
    character: int


@dc.dataclass
class Message:
    symbol: str
    file: str
    severity: str
    message: str
    start: LineCharacter
    end: LineCharacter


def read(file: File) -> dict[str, Any]:
    if isinstance(file, TextIOWrapper):
        return json.load(file)
    else:
        with open(file) as fp:
            return json.load(fp)


def parse_into_messages(d: dict[str, Any]) -> Iterator[Message]:
    for s in d['typeCompleteness']['symbols']:
        for diag in s["diagnostics"]:
            if r := diag.pop("range", None):
                assert sorted(r) == ["end", "start"], r
                start_end = {k: LineCharacter(**v) for k, v in r.items()}
                yield Message(symbol=s["name"], **diag, **start_end)


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    for m in parse_into_messages(read(args[0] if args else sys.stdin)):
        print(json.dumps(dc.asdict(m)))
