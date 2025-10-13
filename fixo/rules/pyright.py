import dataclasses as dc
import json
import re
from functools import cache
from typing import Any, Iterator, cast

from .. import io
from ..edit import Edit
from ..edits import TypeEdit
from ..message import LineCharacter, Message
from ..rule import Rule
from ..tokens.python_file import PythonFile

CATEGORIES = (
    "class",
    "constant",
    "function",
    "method",
    "module",
    "symbol",
    "type alias",
    "type variable",
    "variable",
)


@cache
def parse_into_messages(file: io.FileIdentifier) -> tuple[Message, ...]:
    def messages() -> Iterator[Message]:
        for symbol in io.read_json(file)["typeCompleteness"]["symbols"]:
            base = {"source_name": symbol["name"], "category": symbol["category"]}
            for msg in symbol["diagnostics"]:
                range_: dict[str, Any] = msg.pop("range", None)
                if range_:
                    assert sorted(range_) == ["end", "start"], range_
                    start_end = {k: LineCharacter(**v) for k, v in range_.items()}
                    yield Message(**(base | msg | start_end))

    return tuple(messages())


RETURN_MESSAGES = "Return type is unknown", "Return type annotation is missing"
PARAM_MESSAGES = (
    re.compile('Type of parameter "(.*)" is unknown'),
    re.compile('Type annotation for parameter "(.*)" is missing'),
)


def accept_message(msg: Message, rule: Rule) -> dict[str, Any] | None:
    if rule.categories and msg.category not in rule.categories:
        return None

    if msg.message in RETURN_MESSAGES:
        return {}

    try:
        m = next(m for p in PARAM_MESSAGES if (m := p.match(msg.message)))
    except StopIteration:
        return None
    return {"param": m.group(1)}


def message_to_edits(
    pf: PythonFile, message: Message, rule: Rule, accept: dict[str, Any]
) -> Iterator[TypeEdit]:
    param = accept.get("param", "")
    block = pf.blocks_by_line_number.get(message.start.line)
    context = message, pf.path, accept

    assert block is not None, context
    assert isinstance(param, str), context
    assert message.message.startswith("Type " if param else "Return "), context

    yield TypeEdit(block.full_name, rule.type_name, param)


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    arg = cast(io.FileIdentifier, args[0] if args else sys.stdin)
    for m in parse_into_messages(arg):
        print(json.dumps(dc.asdict(m)))
