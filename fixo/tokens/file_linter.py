from __future__ import annotations

import json
import sys
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING
from typing_extensions import Never

from . import ParseError
from .argument_parser import ArgumentParser
from .messages import LintResult
from .python_file import PythonFile


if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Iterator, Sequence


class ErrorLines:
    """How many lines to display before and after an error"""

    WINDOW = 5
    BEFORE = 2
    AFTER = WINDOW - BEFORE - 1


class FileLinter:
    def _display(self, pf: PythonFile, results: list[LintResult]) -> Iterator[str]:
        """Emit a series of human-readable strings representing the results"""
        for r in results:
            if self.args.lintrunner:
                msg = r.as_message(code=self.code, path=str(pf.path))
                yield json.dumps(msg.asdict(), sort_keys=True)
            else:
                if self.result_shown:
                    yield ""
                else:
                    self.result_shown = True
                if r.line is None:
                    yield f"{pf.path}: {r.name}"
                else:
                    yield from (i.rstrip() for i in self._display_window(pf, r))

    def _display_window(self, pf: PythonFile, r: LintResult) -> Iterator[str]:
        """Display a window onto the code with an error"""
        if r.char is None or not self.report_column_numbers:
            yield f"{pf.path}:{r.line}: {r.name}"
        else:
            yield f"{pf.path}:{r.line}:{r.char + 1}: {r.name}"

        begin = max((r.line or 0) - ErrorLines.BEFORE, 1)
        end = min(begin + ErrorLines.WINDOW, 1 + len(pf.lines))

        for lineno in range(begin, end):
            source_line = pf.lines[lineno - 1].rstrip()
            yield f"{lineno:5} | {source_line}"
            if lineno == r.line:
                spaces = 8 + (r.char or 0)
                carets = len(source_line) if r.char is None else (r.length or 1)
                yield spaces * " " + carets * "^"
