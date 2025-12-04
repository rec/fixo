import dataclasses as dc
import json
import re
from pathlib import Path
from typing import Any, Iterator, cast

from ..blocks.python_file import PythonFile
from ..message import LineCharacter, Message
from ..rule import Rule
from ..type_edit import TypeEdit

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


def parse_into_messages(contents: str) -> tuple[Message, ...]:
    def messages() -> Iterator[Message]:
        for symbol in json.loads(contents)["typeCompleteness"]["symbols"]:
            base = {"source_name": symbol["name"], "category": symbol["category"]}
            for msg in symbol["diagnostics"]:
                range_: dict[str, Any] = msg.pop("range", None)
                if range_:
                    assert sorted(range_) == ["end", "start"], range_
                    start_end = {k: LineCharacter(**v) for k, v in range_.items()}
                    yield Message(**(base | msg | start_end))

    return tuple(messages())


RETURN_RE = re.compile('Return type [^"]*is (unknown|missing)')
PARAM_RE = re.compile('Type .* parameter "(.*)" is (unknown|missing)')


def accept_message(msg: Message, rule: Rule) -> dict[str, Any] | None:
    if rule.categories and msg.category not in rule.categories:
        return None
    if RETURN_RE.match(msg.message):
        return {}
    if m := PARAM_RE.match(msg.message):
        return {"param": m.group(1)}
    return None


def message_to_edits(
    pf: PythonFile, message: Message, rule: Rule, accept: dict[str, Any]
) -> Iterator[TypeEdit]:
    context = message, pf.path, accept
    block = pf.blocks_by_line_number.get(message.start.line)
    assert block is not None, context

    param = accept.get("param", "")
    name = param or block.full_name.rpartition(".")[2] or block.full_name
    if not re.match(rule.name_match, name):
        return

    assert isinstance(param, str), context
    assert message.message.startswith("Type " if param else "Return "), context

    yield TypeEdit(block.full_name, rule.type_name, param)


if __name__ == "__main__":
    import sys

    _, *args = sys.argv
    contents = Path(args[0]).read_text() if args else sys.stdin.read()
    for m in parse_into_messages(contents):
        print(json.dumps(dc.asdict(m)))
