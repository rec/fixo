from __future__ import annotations

import copy
import dataclasses as dc
import importlib
import typing as t
from collections.abc import Sequence
from enum import Enum
from functools import singledispatch
from inspect import signature
from pathlib import Path
from tokenize import TokenInfo
from typing import Any

from . import files
from .edit import Edit
from .importer import Importer, import_dict
from .message import Message
from .tokens.python_file import PythonFile

PREFIX = "fixo.rules"


@t.runtime_checkable
class ParseIntoMessages(t.Protocol):
    def __call__(self, file: files.FileIdentifier) -> t.Iterator[Message]: ...


@t.runtime_checkable
class AcceptMessage(t.Protocol):
    """Return None if we do not accept the message, or a dict with information to be
    passed to `MessageToEdits` otherwise.
    """

    def __call__(self, message: Message, rule: Rule) -> dict[str, t.Any] | None: ...


@t.runtime_checkable
class MessageToEdits(t.Protocol):
    def __call__(
        self, pf: PythonFile, message: Message, rule: Rule, accept: dict[str, t.Any]
    ) -> t.Iterator[Edit]: ...


@dc.dataclass
class Rule:
    categories: Sequence[str]
    type_name: str
    name_match: str

    parse_into_messages: ParseIntoMessages
    accept_message: AcceptMessage
    message_to_edits: MessageToEdits

    def run(self, file: files.FileIdentifier) -> t.Iterator[Edit]:
        file_to_messages: dict[str, list[Message]] = {}
        for message in self.parse_into_messages(file):
            file_to_messages.setdefault(message.file, []).append(message)

        for file, messages in sorted(file_to_messages.items()):
            pf = PythonFile(path=Path(file))
            for m in messages:
                if (a := self.accept_message(m, self)) is not None:
                    yield from self.message_to_edits(pf, m, self, a)

    @staticmethod
    def create_all(d: dict[str, Any]) -> dict[str, Rule]:
        return {k: Rule.create(**v) for k, v in d.items()}

    @staticmethod
    def read_all(f: files.FileIdentifier) -> dict[str, Rule]:
        return Rule.create_all(files.read_json(f))

    @staticmethod
    def create(
        categories: Sequence[str] = (),
        type_name: str = "",
        name_match: str = "",
        parse_into_messages: str = "",
        accept_message: str = "",
        message_to_edits: str = "",
        parent: str = "",
        **kwargs,
    ) -> Rule:
        if parent:
            p = import_dict(parent)
            parse_into_messages = parse_into_messages or p.get(
                "parse_into_messages", ""
            )
            accept_message = accept_message or p.get("accept_message", "")
            message_to_edits = message_to_edits or p.get("message_to_edits", "")

        unset = [k for k, v in locals().items() if k != "parent" and v == ""]
        errors = [f"Not set: {', '.join(unset)}"] if unset else []
        if kwargs:
            errors.append(
                f"Unknown params{'s' * (len(kwargs) != 1)}: {' '.join(kwargs)}"
            )
        if errors:
            raise ValueError("\n".join(["ERROR:", *errors]))

        return Rule(
            categories,
            type_name,
            name_match,
            Importer[ParseIntoMessages]()(PREFIX, parse_into_messages),
            Importer[AcceptMessage]()(PREFIX, accept_message),
            Importer[MessageToEdits]()(PREFIX, message_to_edits),
        )
