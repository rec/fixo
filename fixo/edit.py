from __future__ import annotations

import dataclasses as dc
import typing as t
from tokenize import TokenInfo
from typing import Any, Protocol, Sequence, runtime_checkable

from .importer import Importer
from .tokens.python_file import PythonFile


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


@runtime_checkable
class CreateTokenEdits(Protocol):
    def __call__(self, pf: PythonFile, context: dict[str, Any]) -> TokenEdit: ...


@dc.dataclass
class Edit:
    """
    Abstractly represent an edit as the ability to create TokenEdits
    for a specific list of tokens.

    Edits for a file will probably be stable between different but similar versions
    of that file.
    """

    location: dict[str, Any]
    create_token_edits: CreateTokenEdits

    @staticmethod
    def create(
        location: dict[str, Any],
        create_token_edits: str | CreateTokenEdits,
    ) -> Edit:
        return Edit(location, Importer[CreateTokenEdits]()(create_token_edits))
