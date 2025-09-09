from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tokenize import TokenInfo


NO_TOKEN = -1


class ParseError(ValueError):
    def __init__(self, token: TokenInfo, *args: str) -> None:
        super().__init__(*args)
        self.token = token
