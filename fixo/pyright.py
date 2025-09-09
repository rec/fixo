import dataclasses as dc
import json
from typing import Any, Iterator

from . import data, io


def parse_into_messages(file: io.File) -> Iterator[data.Message]:
    for symbol in io.read_json(file)["typeCompleteness"]["symbols"]:
        for msg in symbol["diagnostics"]:
            range_: dict[str, Any] = msg.pop("range", None)
            if range_:
                assert sorted(range_) == ["end", "start"], range_
                start_end = {k: data.LineCharacter(**v) for k, v in range_.items()}
                yield data.Message(source_name=symbol["name"], **(msg | start_end))


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    for m in parse_into_messages(args[0] if args else sys.stdin):
        print(json.dumps(dc.asdict(m)))
