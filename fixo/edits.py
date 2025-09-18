from __future__ import annotations

import dataclasses as dc
import token
import typing as t
from tokenize import TokenInfo
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from .edit import TokenEdit
from .importer import Importer
from .tokens.block import Block
from .tokens.python_file import PythonFile


def _token_info(type_: int, string: str) -> TokenInfo:
    return TokenInfo(type_, string, (0, 0), (0, 0), string)


@dc.dataclass
class TypeEditData:
    block_name: str
    type_name: str
    type_address: str = ""
    param: str = ""

    @staticmethod
    def from_dict(**kwargs: Any) -> TypeEditData:  # maybe not
        # Throw away unknown elements
        names = {f.name for f in dc.fields(TypeEditData)}
        return TypeEditData(**{k: v for k, v in kwargs.items() if k in names})

    def apply(self, pf: PythonFile) -> Iterator[TokenEdit]:
        yield from _add_import_if_needed(pf, self.type_name, self.type_address)

        b = pf.blocks_by_name[self.block_name]
        assert b.category == "def", b
        for i in range(b.begin, b.dedent + 1):
            t = b.tokens[i]
            if self.param:
                sep = ":"
                accept = (
                    t.type == token.NAME
                    and b.begin < i < b.dedent
                    and b.tokens[i - 1].type in (token.COMMA, token.LPAR)
                    and b.tokens[i + 1].type in (token.COMMA, token.RPAR)
                )
            else:
                sep = " ->"
                accept = t.type == token.RPAR

            if accept:
                yield TokenEdit(i + 1, f"{sep} {self.type_name}")
                return


def _add_import_if_needed(
    pf: PythonFile, type_name: str, type_address: str
) -> Iterator[TokenEdit]:
    type_address = type_address or type_name
    if False:
        yield TokenEdit(1, "")
