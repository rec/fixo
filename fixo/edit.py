from __future__ import annotations

import dataclasses as dc
import typing as t
from collections import Counter
from functools import cached_property
from tokenize import TokenInfo, Untokenizer
from typing import Any, Iterable, Iterator, Protocol, Sequence, runtime_checkable

from .importer import Importer
from .message import Message
from .tokens.python_file import PythonFile


@dc.dataclass(frozen=True, order=True)
class TokenEdit:
    """
    Concretely represents an edit by inserting a string into a list of tokens from a file.

    TokenEdits are rarely stable between different versions of a file, because even
    minor edits will change the location of many tokens.
    """

    position: int
    text: str


def perform_edits(edits: Iterable[TokenEdit], tokens: Iterable[TokenInfo]) -> str:
    """Renders the TokenInfos and TokenEdits for one file into a single string"""
    text_by_position: dict[int, dict[str, None]] = {}
    for e in edits:
        text_by_position.setdefault(e.position, {}).setdefault(e.text, None)

    u = Untokenizer()

    def edit_inserter() -> Iterable[TokenInfo]:
        for i, t in enumerate(tokens):
            # Trick the Untokenizer by adding strings into its record
            u.tokens.extend(text_by_position.get(i, ()))
            yield t

    return u.untokenize(edit_inserter())


@runtime_checkable
class CreateTokenEdits(Protocol):
    def __call__(self, pf: PythonFile, data: dict[str, Any]) -> Iterator[TokenEdit]: ...


@dc.dataclass
class Edit:
    """
    Abstractly represent an edit as the ability to create TokenEdits
    for a specific list of tokens.

    Edits for a file will probably be stable between different but similar versions
    of that file.
    """

    data: dict[str, Any]
    create_token_edits: CreateTokenEdits

    @staticmethod
    def create(
        data: dict[str, Any],
        create_token_edits: str | CreateTokenEdits,
    ) -> Edit:
        imp = Importer[CreateTokenEdits]()("fixo.edits", create_token_edits)
        return Edit(data, imp)
