import dataclasses as dc
import importlib
from collections.abc import Sequence
from enum import Enum
from tokenize import TokenInfo
from typing import Any, Callable, Iterator, Protocol, TypeAlias, cast

from . import data, io
from .tokens.python_file import PythonFile

BASE_ADDRESS = "fixo.rules"


@dc.dataclass
class TokenEdit:
    """
    Concretely represents an edit as surgery on a list of tokens from a file.

    TokenEdits are rarely stable between different versions of a file, because even
    minor edits will change the location of many tokens.
    """

    to_replace: slice
    replacement: Sequence[TokenInfo]

    def apply(self, tokens: list[TokenInfo]):
        tokens[self.to_replace] = self.replacement


"""
NOTE: some features here are implemented with callable class members which are imported
at runtime by name, rather than an abstract method, so that these members can be
customized by the user with their own code.
"""


def _to_callable(address: str) -> Callable[..., Any]:
    if address.startswith("."):
        address = BASE_ADDRESS + address
    module, _, name = address.rpartition(".")
    c = getattr(importlib.import_module(module), name)
    assert callable(c)
    return c


def _call(address: str, *args: Any, **kwargs: Any) -> Any:
    return _to_callable(address)(*args, **kwargs)


def _callable_dict(d: dict[str, Callable | str | None]) -> dict[str, Callable | None]:
    return {k: (_to_callable(v) if isinstance(v, str) else v) for k, v in d.items()}


class CreateTokenEdits(Protocol):
    def __call__(self, pf: PythonFile, data: str): ...


@dc.dataclass
class Edit:
    """
    Abstractly represent an edit as the ability to create TokenEdits
    for a specific list of tokens.

    Edits for a file will probably be stable between different but similar versions
    of that file.
    """

    location: str
    create_token_edits: CreateTokenEdits

    @staticmethod
    def create(location: str, create_token_edits: CreateTokenEdits | str) -> Edit:
        if isinstance(create_token_edits, str):
            create_token_edits = cast(
                CreateTokenEdits, _to_callable(create_token_edits)
            )
        return Edit(location, create_token_edits)


class ParseIntoMessages(Protocol):
    def __call__(self, file: io.File) -> Iterator[data.Message]: ...


class AcceptMessage(Protocol):
    def __call__(self, message: data.Message, data: Any) -> bool: ...


class MessageToEdits(Protocol):
    def __call__(self, pf: PythonFile, message: data.Message) -> Iterator[Edit]: ...


@dc.dataclass
class Rule:
    parse_into_messages: ParseIntoMessages | None = None
    accept_message: AcceptMessage | None = None
    message_to_edits: MessageToEdits | None = None

    @staticmethod
    def create(*, parent: str | None = None, **kwargs: Any) -> Rule:
        if parent is not None:
            c = _call(parent)
            kwargs = (c if isinstance(c, dict) else dc.asdict(c)) | kwargs

        return Rule(**_callable_dict(kwargs))
