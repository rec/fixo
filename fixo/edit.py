from __future__ import annotations

import dataclasses as dc
import typing as t
from collections import Counter
from functools import cached_property
from tokenize import TokenInfo, Untokenizer
from typing import Any, Iterable, Iterator, Protocol, Sequence, runtime_checkable

from .blocks.python_file import PythonFile
from .importer import Importer
from .message import Message
from .token_edit import TokenEdit


@runtime_checkable
class CreateTokenEdits(Protocol):
    # TODO: temporarily not used
    def __call__(self, pf: PythonFile, data: dict[str, Any]) -> Iterator[TokenEdit]: ...


@dc.dataclass
class Edit:
    """
    # TODO: temporarily not used
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
