from __future__ import annotations

import dataclasses as dc
import importlib
import typing
from collections.abc import Sequence
from enum import Enum
from inspect import signature
from tokenize import TokenInfo
from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    runtime_checkable,
)

from typing_extensions import TypeIs

from . import data, io
from .tokens.python_file import PythonFile

_T = TypeVar("_T")
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


def _load_symbol(address: str) -> Any:
    if address.startswith("."):
        address = BASE_ADDRESS + address
    module, _, name = address.rpartition(".")
    return getattr(importlib.import_module(module), name)


class Loader(Generic[_T]):
    def __init__(self):
        self._T = typing.get_args(getattr(self, "__orig_class__", None))[0]

    def __call__(self, address: Any) -> _T:
        if isinstance(address, str):
            address = _load_symbol(address)
        if isinstance(address, self._T):
            return address
        raise TypeError(f"Expected type {self._T} but got {address}")


@runtime_checkable
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
    def create(location: str, create_token_edits: str | CreateTokenEdits) -> Edit:
        return Edit(location, Loader[CreateTokenEdits]()(create_token_edits))


@runtime_checkable
class ParseIntoMessages(Protocol):
    def __call__(self, file: io.File) -> Iterator[data.Message]: ...


@runtime_checkable
class AcceptMessage(Protocol):
    def __call__(self, message: data.Message, data: Any) -> bool: ...


@runtime_checkable
class MessageToEdits(Protocol):
    def __call__(self, pf: PythonFile, message: data.Message) -> Iterator[Edit]: ...


def _to_dict(x: Any) -> dict[str, Any]:
    if callable(x):
        x = x()
    if isinstance(x, dict):
        return x
    try:
        return dc.asdict(x)
    except Exception:
        return dict(x.__dict__)


@dc.dataclass
class Rule:
    parse_into_messages: ParseIntoMessages | None = None
    accept_message: AcceptMessage | None = None
    message_to_edits: MessageToEdits | None = None

    @staticmethod
    def create(
        *,
        parent: str | None = None,
        parse_into_messages: str | None = None,
        accept_message: str | None = None,
        message_to_edits: str | None = None,
    ) -> Rule:
        rule = Rule()
        if parse_into_messages is not None:
            rule.parse_into_messages = Loader[ParseIntoMessages]()(parse_into_messages)
        if accept_message is not None:
            rule.accept_message = Loader[AcceptMessage]()(accept_message)
        if message_to_edits is not None:
            rule.message_to_edits = Loader[MessageToEdits]()(message_to_edits)
        if parent:
            for k, v in _to_dict(_load_symbol(parent)).items():
                if not getattr(rule, k, True):
                    setattr(rule, k, v)
        return rule
