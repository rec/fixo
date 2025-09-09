from __future__ import annotations

import token
from functools import cached_property
from pathlib import Path
from tokenize import TokenInfo, generate_tokens
from typing import TYPE_CHECKING

from typing_extensions import Self

from . import NO_TOKEN, ParseError
from .blocks import EMPTY_TOKENS, blocks

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .block import Block


class PythonFile:
    contents: str
    lines: list[str]
    path: Path | None

    def __init__(
        self,
        path: Path | None = None,
        contents: str | None = None,
    ) -> None:
        self.path = path
        if contents is None and path is not None:
            contents = path.read_text()

        self.contents = contents or ""
        self.lines = self.contents.splitlines(keepends=True)

    @classmethod
    def make(cls, pc: Path | str | None = None) -> Self:
        return cls(path=pc) if isinstance(pc, Path) else cls(contents=pc)

    def with_contents(self, contents: str) -> Self:
        return self.__class__(self.path, contents)

    @cached_property
    def tokens(self) -> list[TokenInfo]:
        # Might raise IndentationError if the code is mal-indented
        return list(generate_tokens(iter(self.lines).__next__))

    @cached_property
    def token_lines(self) -> list[list[TokenInfo]]:
        """Returns lists of TokenInfo segmented by token.NEWLINE"""
        token_lines: list[list[TokenInfo]] = [[]]

        for t in self.tokens:
            if t.type not in (token.COMMENT, token.ENDMARKER, token.NL):
                token_lines[-1].append(t)
                if t.type == token.NEWLINE:
                    token_lines.append([])
        if token_lines and not token_lines[-1]:
            token_lines.pop()
        return token_lines

    @cached_property
    def import_lines(self) -> list[list[int]]:
        froms, imports = [], []
        for i, (t, *_) in enumerate(self.token_lines):
            if t.type == token.INDENT:
                break
            if t.type == token.NAME:
                if t.string == "from":
                    froms.append(i)
                elif t.string == "import":
                    imports.append(i)

        return [froms, imports]

    @cached_property
    def opening_comment_lines(self) -> int:
        """The number of comments at the very top of the file."""
        it = (i for i, s in enumerate(self.lines) if not s.startswith("#"))
        return next(it, 0)

    def __getitem__(self, i: int | slice) -> TokenInfo | Sequence[TokenInfo]:
        return self.tokens[i]

    def next_token(self, start: int, token_type: int, error: str) -> int:
        for i in range(start, len(self.tokens)):
            if self.tokens[i].type == token_type:
                return i
        raise ParseError(self.tokens[-1], error)

    def docstring(self, start: int) -> str:
        for i in range(start + 1, len(self.tokens)):
            tk = self.tokens[i]
            if tk.type == token.STRING:
                return tk.string
            if tk.type not in EMPTY_TOKENS:
                return ""
        return ""

    @cached_property
    def indent_to_dedent(self) -> dict[int, int]:
        dedents = dict[int, int]()
        stack = list[int]()

        for i, t in enumerate(self.tokens):
            if t.type == token.INDENT:
                stack.append(i)
            elif t.type == token.DEDENT:
                dedents[stack.pop()] = i

        return dedents

    @cached_property
    def errors(self) -> dict[str, str]:
        return {}

    @cached_property
    def insert_import_line(self) -> int | None:
        froms, imports = self.import_lines
        if section := froms + imports:
            return max(section) + 1
        return self.opening_comment_lines + 1

    @cached_property
    def blocks(self) -> list[Block]:
        res = blocks(self.tokens)
        self.errors.update(res.errors)
        return res.blocks
