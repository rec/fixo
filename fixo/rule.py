from __future__ import annotations

import dataclasses as dc
import re
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator, Protocol, runtime_checkable

from .blocks.python_file import PythonFile
from .importer import Importer, import_dict
from .message import Message
from .type_edit import TypeEdit

PREFIX = "fixo.rules"


@runtime_checkable
class ParseIntoMessages(Protocol):
    def __call__(self, contents: str) -> Iterator[Message]: ...


@runtime_checkable
class AcceptMessage(Protocol):
    """Return None if we do not accept the message, or a dict with information to be
    passed to `MessageToEdits` otherwise.
    """

    def __call__(self, message: Message, rule: Rule) -> dict[str, Any] | None: ...


@runtime_checkable
class MessageToEdits(Protocol):
    def __call__(
        self,
        pf: PythonFile,
        message: Message,
        rule: Rule,
        accept: dict[str, Any],
    ) -> Iterator[TypeEdit]: ...


@dc.dataclass
class Rule:
    categories: Sequence[str]
    type_name: str
    name_match: str

    parse_into_messages: ParseIntoMessages
    accept_message: AcceptMessage
    message_to_edits: MessageToEdits

    def edits(self, file_messages: dict[str, list[Message]]) -> Iterator[TypeEdit]:
        for file, messages in file_messages.items():
            pf = PythonFile(path=Path(file))
            for m in messages:
                if (a := self.accept_message(m, self)) is not None:
                    yield from self.message_to_edits(pf, m, self, a)

    def file_messages(self, contents: str) -> dict[str, list[Message]]:
        file_messages: dict[str, list[Message]] = {}
        for message in self.parse_into_messages(contents):
            file_messages.setdefault(message.file, []).append(message)
        return dict(sorted(file_messages.items()))

    @cached_property
    def matches(self) -> re.Pattern:
        return re.compile(self.name_match)

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
                "parse_into_messages",
                "",
            )
            accept_message = accept_message or p.get("accept_message", "")
            message_to_edits = message_to_edits or p.get("message_to_edits", "")

        unset = [k for k, v in locals().items() if k != "parent" and v == ""]
        errors = [f"Not set: {', '.join(unset)}"] if unset else []
        if kwargs:
            errors.append(
                f"Unknown params{'s' * (len(kwargs) != 1)}: {' '.join(kwargs)}",
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
