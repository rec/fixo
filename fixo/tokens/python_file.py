from __future__ import annotations

import token
from functools import cached_property
from pathlib import Path
from tokenize import TokenInfo, generate_tokens
from typing import TYPE_CHECKING

from typing_extensions import Self

from . import NO_TOKEN, ParseError
from .blocks import EMPTY_TOKENS, IGNORED_TOKENS, BlocksResult, blocks

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .block import Block


class PythonFile:
    contents: str
    lines: list[str]
    path: Path | None

    def __init__(
        self,
        *,
        path: Path | None = None,
        contents: str | None = None,
    ) -> None:
        self.path = path
        if contents is None and path is not None:
            contents = path.read_text()

        self.contents = contents or ""
        self.lines = self.contents.splitlines(keepends=True)

    @cached_property
    def blocks(self) -> BlocksResult:
        return blocks(self.tokens)

    @cached_property
    def tokens(self) -> list[TokenInfo]:
        # Might raise IndentationError if the code is mal-indented
        return list(generate_tokens(iter(self.lines).__next__))

    @cached_property
    def line_ranges(self) -> list[range]:
        ranges = list[range]()

        first = None
        last = -1
        for i, t in enumerate(self.tokens):
            if t.type in IGNORED_TOKENS:
                continue
            if first is None:
                first = i
            if t.type == token.NEWLINE:
                ranges.append(range(first, last + 1))
                first = None
            last = i

        return ranges

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
    def token_lines(self) -> list[list[TokenInfo]]:
        # deprecated in favor of self.line_ranges()
        """Returns lists of TokenInfo segmented by token.NEWLINE.
        Removes IGNORED_TOKENS (comments, encodings, endmarkers).
        Cannot be used to reconstitute
        """
        token_lines: list[list[TokenInfo]] = [[]]

        for t in self.tokens:
            if t.type not in IGNORED_TOKENS:
                token_lines[-1].append(t)
                if t.type == token.NEWLINE:
                    token_lines.append([])
        if token_lines and not token_lines[-1]:
            token_lines.pop()
        return token_lines

    @cached_property
    def import_lines(self) -> list[list[int]]:
        froms, imports = [], []
        for i, tl in enumerate(self.token_lines):
            t = tl[0]
            if t.type == token.INDENT:
                break
            elif t.type != token.NAME:
                continue
            elif t.string == "from":
                froms.append(i)
            elif t.string == "import":
                imports.append(i)

        return [froms, imports]

    @cached_property
    def opening_comment_lines(self) -> int:
        """The number of comments at the very top of the file."""
        # TODO: should use the logical lines, not the text lines
        it = (i for i, s in enumerate(self.lines) if not s.startswith("#"))
        return next(it, 0)

    def docstring(self, start: int) -> str:
        for i in range(start + 1, len(self.tokens)):
            tk = self.tokens[i]
            if tk.type == token.STRING:
                return tk.string
            if tk.type not in EMPTY_TOKENS:
                return ""
        return ""

    def insert_import_line(self) -> int:
        """The first line you can use to insert an import"""
        froms, imports = self.import_lines
        if section := froms + imports:
            return max(section) + 1
        return self.opening_comment_lines + 1
