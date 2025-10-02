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

from . import io
from .edit import Edit
from .importer import Importer, import_dict
from .message import Message
from .tokens.python_file import PythonFile


@t.runtime_checkable
class ParseIntoMessages(t.Protocol):
    def __call__(self, file: io.FileIdentifier) -> t.Iterator[Message]: ...


@t.runtime_checkable
class AcceptMessage(t.Protocol):
    def __call__(self, message: Message, context: dict[str, t.Any]) -> bool: ...


@t.runtime_checkable
class MessageToEdits(t.Protocol):
    def __call__(
        self, pf: PythonFile, message: Message, context: dict[str, t.Any]
    ) -> t.Iterator[Edit]: ...


@dc.dataclass
class Rule:
    parse_into_messages: ParseIntoMessages
    accept_message: AcceptMessage
    message_to_edits: MessageToEdits
    context: dict[str, t.Any]

    def run(self, file: io.FileIdentifier) -> t.Iterator[Edit]:
        file_to_messages = dict[str, list[Message]]()
        for message in self.parse_into_messages(file):
            file_to_messages.setdefault(message.file, []).append(message)

        for file, messages in sorted(file_to_messages.items()):
            pf = PythonFile(path=Path(file))
            for m in messages:
                if self.accept_message(m, self.context):
                    yield from self.message_to_edits(pf, m, self.context)

    @staticmethod
    def read(f: io.FileIdentifier) -> dict[str, Rule]:
        return {k: Rule.create(**v) for k, v in io.read_json(f).items()}

    @staticmethod
    def create(
        parse_into_messages: str | None = None,
        accept_message: str | None = None,
        message_to_edits: str | None = None,
        context: dict[str, t.Any] | None = None,
        parent: str | None = None,
    ) -> Rule:
        d = dict(locals())
        if parent:
            p = import_dict(parent)
            parse_into_messages = parse_into_messages or p.get("parse_into_messages")
            accept_message = accept_message or p.get("accept_message")
            message_to_edits = message_to_edits or p.get("message_to_edits")
        else:
            p = {}

        if not (parse_into_messages and accept_message and message_to_edits):
            missing = ", ".join(
                ["parse_into_messages"] * (not parse_into_messages)
                + ["accept_message"] * (not accept_message)
                + ["message_to_edits"] * (not message_to_edits)
            )
            raise ValueError(f"Not set: {missing}")

        if context is None:
            context = {}
        context.update(p.get("context", {}))

        prefix = "fixo.rules"
        return Rule(
            Importer[ParseIntoMessages]()(prefix, parse_into_messages),
            Importer[AcceptMessage]()(prefix, accept_message),
            Importer[MessageToEdits]()(prefix, message_to_edits),
            context,
        )
