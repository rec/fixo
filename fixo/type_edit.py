from __future__ import annotations

import dataclasses as dc
import itertools
import token
import typing as ty
from tokenize import TokenInfo
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from .blocks.block import Block
from .blocks.imports import Import
from .blocks.python_file import PythonFile
from .importer import Importer
from .token_edit import TokenEdit, perform_edits


@dc.dataclass
class TypeEdit:
    """Add a type to a function, or to one of its parameters"""

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
            type_name = next(i for i in pf.imports if i.address == self.type_name).as_
        except StopIteration:
            address, _, type_name = self.type_name.rpartition(".")
            if address:
                if self.prefer_as:
                    import_line = f"\nimport {self.type_name} as {type_name}\n"
                else:
                    import_line = f"\nfrom {address} import {type_name}\n"
                yield TokenEdit(pf.insert_import_token, import_line)

        edit_position = self._edit_position(pf)
        sep = ":" if self.param else "->"
        if pf.tokens[edit_position + 1] != sep:
            space = "" if self.param else " "
            yield TokenEdit(edit_position, f"{space}{sep} {type_name}")

    def _edit_position(self, pf: PythonFile) -> int:
        b = pf.blocks_by_name[self.function_name]
        if b.category != "def":
            raise ValueError(f"Cannot apply a rule {self} to a class {b}")

        it = range(b.begin, len(pf.tokens))
        begin = next(i for i in it if pf.tokens[i].string == "(")
        prev = begin
        depth = 0

        for i in range(begin, len(pf.tokens) - 1):
            t = pf.tokens[i]
            depth += (t.string in ("{", "(", "[")) - (t.string in ("}", ")", "]"))
            if not (self.param or depth):
                return i + 1
            if self.param and (depth == 0 or depth == 1 and t.string == ","):
                for j in range(prev + 1, i):
                    u = pf.tokens[j]
                    if u.string == self.param:
                        return i
                    elif u.type != token.COMMENT:
                        break
                prev = i
        raise ValueError(f"Did not find {self}")

    def asdict(self) -> dict[str, Any]:
        return {k: v for k, v in dc.asdict(self).items() if v}


def perform_type_edits(type_edits: ty.Iterable[TypeEdit], pf: PythonFile) -> str:
    edits = itertools.chain.from_iterable(e.apply(pf) for e in type_edits)

    return perform_edits(edits, pf.tokens)
