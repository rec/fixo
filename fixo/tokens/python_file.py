from __future__ import annotations

import token
from functools import cached_property
from itertools import groupby
from pathlib import Path
from tokenize import TokenInfo, generate_tokens
from typing import TYPE_CHECKING

from typing_extensions import Self

from . import EMPTY_TOKENS, NO_TOKEN, ParseError, is_ignored
from .blocks import BlocksResult, blocks
from .imports import Import

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
    def blocks(self) -> list[Block]:
        return self._blocks_and_errors.blocks

    @cached_property
    def blocks_by_name(self) -> dict[str, Block]:
        return {b.full_name: b for b in self.blocks}

    @cached_property
    def blocks_by_line_number(self) -> dict[int, Block]:
        # Lines that don't appear are in the top-level scope
        # Later blocks correctly overwrite earlier, parent blocks.
        return {i: b for b in self.blocks for i in b.line_range}

    @cached_property
    def errors(self) -> dict[str, str]:
        return self._blocks_and_errors.errors

    @cached_property
    def tokens(self) -> list[TokenInfo]:
        # Might raise IndentationError if the code is mal-indented
        return list(generate_tokens(iter(self.lines).__next__))

    @cached_property
    def token_lines(self) -> list[list[TokenInfo]]:
        # Gives a range of logical lines split by newlines
        return [list(g) for k, g in groupby(self.tokens, _is_line_separator) if not k]

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
    def imports(self) -> list[Import]:
        return [i for tl in self.token_lines for i in Import.create(tl)]

    @cached_property
    def opening_comment_lines(self) -> int:
        """The number of comments at the very top of the file."""
        return next((t.start[0] - 1 for t in self.tokens if is_ignored(t)), 0)

    @cached_property
    def insert_import_token(self) -> int:
        """The token you can use to insert an import before"""
        if self.imports:
            line = self.imports[-1].line_number
        else:
            line = self.opening_comment_lines + 1
        return next(i for i, t in enumerate(self.tokens) if t.start[0] == line)

    @cached_property
    def _blocks_and_errors(self) -> BlocksResult:
        return blocks(self.tokens)


def _is_line_separator(t: TokenInfo) -> bool:
    return t.type == token.NEWLINE or t.string == ";"
