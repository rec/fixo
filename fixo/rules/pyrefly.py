import json
import re
from collections.abc import Iterator
from typing import Any

from ..blocks.python_file import PythonFile
from ..message import LineCharacter, Message
from ..rule import Rule
from ..type_edit import TypeEdit

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

            if not func["return_annotation"]:
                yield msg(func, "")

            for param in func["parameters"]:
                if not param["annotation"]:
                    yield msg(param, param["name"])


def accept_message(msg: Message, rule: Rule) -> dict[str, Any] | None:
    # is_param = bool(msg.message)
    return {"param": msg.message}


def message_to_edits(
    pf: PythonFile,
    message: Message,
    rule: Rule,
    accept: dict[str, Any],
) -> Iterator[TypeEdit]:
    if re.match(rule.name_match, message.base_name):
        yield TypeEdit(message.name, rule.type_name, accept["param"])
