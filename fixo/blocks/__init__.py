from __future__ import annotations

import token
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tokenize import TokenInfo


__all__ = [
    "Block",
    "is_empty",
    "ParseError",
    "PythonFile",
]

NO_TOKEN = -1

# Python 3.12 and up have two new token types, FSTRING_START and FSTRING_END
_START_OF_LINE_TOKENS = token.DEDENT, token.INDENT, token.NEWLINE
_IGNORED_TOKENS = token.COMMENT, token.ENDMARKER, token.ENCODING, token.NL
_EMPTY_TOKENS = dict.fromkeys(_START_OF_LINE_TOKENS + _IGNORED_TOKENS)

_LINTER = Path(__file__).absolute().parents[0]


class ParseError(ValueError):
    def __init__(self, token: TokenInfo, *args: str) -> None:
        super().__init__(*args)
        self.token = token


def is_empty(t: TokenInfo) -> bool:
    return t.type in _EMPTY_TOKENS


from .block import Block
from .python_file import PythonFile
