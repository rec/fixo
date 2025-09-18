from __future__ import annotations

import token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tokenize import TokenInfo


NO_TOKEN = -1

# Python 3.12 and up have two new token types, FSTRING_START and FSTRING_END
_START_OF_LINE_TOKENS = token.DEDENT, token.INDENT, token.NEWLINE
IGNORED_TOKENS = token.COMMENT, token.ENDMARKER, token.ENCODING, token.NL
EMPTY_TOKENS = dict.fromkeys(_START_OF_LINE_TOKENS + IGNORED_TOKENS)


class ParseError(ValueError):
    def __init__(self, token: TokenInfo, *args: str) -> None:
        super().__init__(*args)
        self.token = token
