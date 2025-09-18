from __future__ import annotations

import dataclasses as dc
import itertools
import typing as t
from collections import Counter
from functools import cached_property
from tokenize import TokenInfo
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


def perform_edit(edits: Iterator[TokenEdit], tokens: Sequence[TokenInfo]) -> str:
    if dupes := [k for k, v in Counter(e.position for e in edits).items() if v > 1]:
        raise ValueError(f"Duplicate edits on position: {dupes}")

    edits_ = sorted(edits, reverse=True)
    ut = tokenize.Untokenizer()

    def token_iterator() -> Iterable[TokenInfo]:
        for i, tok in enumerate(tokens):
            if edits_ and edits_[-1].position == i:
                # Trick the Untokenizer by adding strings into its record
                un.tokens.append(edits_.pop())
            yield tok

    return ut.untokenize(token_iterator())


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
