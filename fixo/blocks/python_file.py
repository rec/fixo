from __future__ import annotations

import token
from functools import cached_property
from pathlib import Path
from tokenize import TokenInfo, generate_tokens
from typing import TYPE_CHECKING

from typing_extensions import Self

from . import NO_TOKEN, ParseError, is_empty
from .imports import Import

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .block import Block


class PythonFile:
    linter_name: str

    def __init__(self, path: Path, *, contents: str | None = None) -> None:
        self._contents = contents
        self._path = path

    def __repr__(self) -> str:
        return f"PythonFile({self._path})"

    @cached_property
    def contents(self) -> str:
        if self._contents is not None:
            return self._contents
        return self.path.read_text() if self._path else ""

    @cached_property
    def lines(self) -> list[str]:
        return self.contents.splitlines(keepends=True)

    @cached_property
    def path(self) -> Path:
        assert self._path is not None
        return self._path

    def with_contents(self, contents: str) -> Self:
        return self.__class__(contents=contents, path=self._path)

    @cached_property
    def tokens(self) -> list[TokenInfo]:
        """This file, tokenized. Raises IndentationError on badly indented code."""
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
            if is_empty(tk):
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
    def imports(self) -> list[Import]:
        return [i for tl in self.token_lines for i in Import.create(tl)]

    @cached_property
    def blocks(self) -> list[Block]:
        from .blocks import blocks

        return blocks(self)

    @cached_property
    def blocks_by_line_number(self) -> dict[int, Block]:
        # Lines that don't appear are in the top-level scope
        # Later blocks correctly overwrite earlier, parent blocks.
        return {i: b for b in self.blocks for i in b.line_range}

    @cached_property
    def blocks_by_name(self) -> dict[str, Block]:
        return {b.full_name: b for b in self.blocks}

    def block_name(self, line: int) -> str:
        block = self.blocks_by_line_number.get(line)
        return block.full_name if block else ""

    @cached_property
    def insert_import_token(self) -> int:
        """The token you can use to insert an import before"""
        if self.imports:
            line = self.imports[-1].line_number
        else:
            line = self.opening_comment_lines
        return next(i for i, t in enumerate(self.tokens) if t.start[0] == line + 1)

    @cached_property
    def is_public(self) -> bool:
        return is_public(*self.python_parts)

    @cached_property
    def python_parts(self) -> tuple[str, ...]:
        parts = self.path.with_suffix("").parts
        return parts[:-1] if parts[-1] == "__init__" else parts


def is_public(*parts: str) -> bool:
    # TODO: this rule is easy to understand but incomplete.
    #
    # What is missing is checking `__all__`: see
    # https://github.com/pytorch/pytorch/wiki/Public-API-definition-and-documentation

    it = (s for p in parts for s in p.split("."))
    return not any(i.startswith("_") and not i.startswith("__") for i in it)
