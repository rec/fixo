import dataclasses as dc
import json
from typing import Any, Iterator, cast

from .. import io
from ..edit import Edit
from ..message import LineCharacter, Message
from ..tokens.python_file import PythonFile


def parse_into_messages(file: io.File) -> Iterator[Message]:
    for symbol in io.read_json(file)["typeCompleteness"]["symbols"]:
        for msg in symbol["diagnostics"]:
            range_: dict[str, Any] = msg.pop("range", None)
            if range_:
                assert sorted(range_) == ["end", "start"], range_
                start_end = {k: LineCharacter(**v) for k, v in range_.items()}
                yield Message(source_name=symbol["name"], **(msg | start_end))


def accept_message(msg: Message, context: dict[str, Any] | None) -> bool:
    if context:
        for k, v in context.items():
            vm = getattr(msg, k, None)
            if isinstance(v, str) and not (isinstance(vm, str) and v in vm):
                return False
            elif v != vm:
                return False
    return True


def message_to_edits(pf: PythonFile, message: Message) -> Iterator[Edit]:
    if False:
        yield Edit.create()


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    arg = cast(io.File, args[0] if args else sys.stdin)
    for m in parse_into_messages(arg):
        print(json.dumps(dc.asdict(m)))
