from __future__ import annotations

import dataclasses as dc
import token
import typing as t
from tokenize import TokenInfo
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from .edit import TokenEdit
from .importer import Importer
from .tokens.block import Block
from .tokens.imports import Import
from .tokens.python_file import PythonFile


def _token_info(type_: int, string: str) -> TokenInfo:
    return TokenInfo(type_, string, (0, 0), (0, 0), string)


class ImportEdit(t.NamedTuple):
    edit: TokenEdit | None
    type_name: str


@dc.dataclass
class TypeEdit:
    """Add a return or parameter type to a function"""

    # Full "block name" of the function (see tokens/blocks.py)
    function_name: str

    # Full Python path to the type, with modules separated by dots
    type_address: str

    # Name of the param getting a new type: empty means a return type is being added
    param: str = ""

    # If True, use `import torch.Tensor as Tensor`, otherwise `from torch import Tensor`
    prefer_as: bool = False

    def apply(self, pf: PythonFile) -> Iterator[TokenEdit]:
        try:
            imp = next(i for i in pf.imports if i.address == self.type_address)
        except StopIteration:
            address, _, type_name = self.type_address.rpartition(".")
            if self.prefer_as:
                import_line = f"import {self.type_address} as {type_name}\n"
            else:
                import_line = f"from {address} import {type_name}\n"
            yield TokenEdit(pf.insert_import_token, import_line)
        else:
            type_name = imp.as_

        b = pf.blocks_by_name[self.function_name]
        assert b.category == "def", b
        for i in range(b.begin, b.dedent + 1):
            if self._accept(b, i):
                sep = ":" if self.param else " ->"
                yield TokenEdit(i + 1, f"{sep} {type_name}")
                return

    def _accept(self, b: Block, i: int) -> bool:
        tok = b.tokens[i]
        if self.param:
            return (
                b.begin < i < b.dedent
                and tok.type == token.NAME
                and b.tokens[i - 1].type in (token.COMMA, token.LPAR)
                and b.tokens[i + 1].type in (token.COMMA, token.RPAR)
            )
        else:
            return tok.type == token.RPAR
