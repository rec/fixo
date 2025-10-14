from __future__ import annotations

import dataclasses as dc
import itertools
import token
import typing as t
from tokenize import TokenInfo
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from .edit import TokenEdit, perform_edits
from .importer import Importer
from .tokens.block import Block
from .tokens.imports import Import
from .tokens.python_file import PythonFile


class ImportEdit(t.NamedTuple):
    edit: TokenEdit | None
    type_name: str


@dc.dataclass
class TypeEdit:
    """Add a return or parameter type to a function"""

    # Full "block name" of the function (see tokens/blocks.py)
    function_name: str

    # Full Python path to the type, with modules separated by dots
    type_name: str

    # Name of the param getting a new type: empty means a return type is being added
    param: str = ""

    # If True, use `import torch.Tensor as Tensor`, otherwise `from torch import Tensor`
    prefer_as: bool = False

    def apply(self, pf: PythonFile) -> Iterator[TokenEdit]:
        try:
            imp = next(i for i in pf.imports if i.address == self.type_name)
        except StopIteration:
            address, _, type_name = self.type_name.rpartition(".")
            if address:
                if self.prefer_as:
                    import_line = f"import {self.type_name} as {type_name}\n\n"
                else:
                    import_line = f"from {address} import {type_name}\n\n"
                yield TokenEdit(pf.insert_import_token, import_line)
        else:
            type_name = imp.as_

        b = pf.blocks_by_name[self.function_name]
        assert b.category == "def", (b, self.function_name)
        for i in range(b.begin, b.dedent + 1):
            if self._accept(b, i):
                sep = ":" if self.param else " ->"
                yield TokenEdit(i + 1, f"{sep} {type_name}")
                return
        raise ValueError(f"FAILED to apply {self}: should never get here")

    def _accept(self, b: Block, i: int) -> bool:
        tok = b.tokens[i]
        if self.param:
            return (
                b.begin < i < b.dedent
                and tok.type == token.NAME
                and b.tokens[i - 1].string in "(,"
                and b.tokens[i + 1].string in ",)"
            )
        else:
            return tok.string == ")"


def perform_type_edits(type_edits: t.Iterator[TypeEdit], pf: PythonFile) -> str:
    edits = itertools.chain.from_iterable(e.apply(pf) for e in type_edits)

    return perform_edits(edits, pf.tokens)
