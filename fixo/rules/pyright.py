import dataclasses as dc
import json
import re
from functools import cache
from typing import Any, Iterator, cast

from .. import io
from ..edit import Edit
from ..message import LineCharacter, Message
from ..tokens.python_file import PythonFile

_MATCH_UNKNOW_PARAM = re.compile('Type of parameter "(.*)" is unknown').match


@cache
def parse_into_messages(file: io.FileIdentifier) -> tuple[Message, ...]:
    def messages() -> Iterator[Message]:
        for symbol in io.read_json(file)["typeCompleteness"]["symbols"]:
            for msg in symbol["diagnostics"]:
                range_: dict[str, Any] = msg.pop("range", None)
                if range_:
                    assert sorted(range_) == ["end", "start"], range_
                    start_end = {k: LineCharacter(**v) for k, v in range_.items()}
                    yield Message(source_name=symbol["name"], **(msg | start_end))

    return tuple(messages())


def accept_message(msg: Message, context: dict[str, Any]) -> bool:
    m = msg.message
    return m == "Return type is unknown" or (
        m.startswith("Type of parameter ") and m.endswith(" is unknown")
    )


def message_to_edits(
    pf: PythonFile, message: Message, context: dict[str, Any]
) -> Iterator[Edit]:
    if False:
        yield Edit.create({}, "none")


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    arg = cast(io.FileIdentifier, args[0] if args else sys.stdin)
    for m in parse_into_messages(arg):
        print(json.dumps(dc.asdict(m)))
