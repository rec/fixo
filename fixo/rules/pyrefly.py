import json
import re
from collections.abc import Iterator
from typing import Any

from ..blocks.python_file import PythonFile
from ..message import LineCharacter, Message
from ..rule import Rule
from ..type_edit import TypeEdit

SPECIAL_NAMES = "cls", "self"

type_command_string = "pyrefly report"


def parse_into_messages(contents: str) -> Iterator[Message]:
    d = json.loads(contents)
    for file, file_contents in d.items():
        for func in file_contents["functions"]:
            name = func["name"]
            kwargs = {"name": name, "file": file, "severity": "", "category": ""}

            def msg(d: dict[str, Any], message: str) -> Message:
                loc = d["location"]
                start = LineCharacter(loc["start"]["line"], loc["start"]["column"])
                end = LineCharacter(loc["end"]["line"], loc["end"]["column"])
                return Message(message=message, start=start, end=end, **kwargs)

            if not (func["return_annotation"] or name.split(".")[-1].startswith("__")):
                yield msg(func, "")

            for param in func["parameters"]:
                pa, pn = param["annotation"], param["name"]
                if not (pa or pn in SPECIAL_NAMES or pn.startswith("_")):
                    yield msg(param, pn)


def accept_message(msg: Message, rule: Rule) -> dict[str, Any] | None:
    return {"param": msg.message}


def message_to_edits(
    pf: PythonFile,
    message: Message,
    rule: Rule,
    accept: dict[str, Any],
) -> Iterator[TypeEdit]:
    if re.match(rule.name_match, message.base_name):
        yield TypeEdit(message.name, rule.type_name, accept["param"])
