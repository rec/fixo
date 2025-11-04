from __future__ import annotations

import argparse
import contextlib
import dataclasses as dc
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from functools import cache, cached_property, partial, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Sequence, TypeVar, cast

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterable


_PYRIGHT = "pyright --ignoreexternal --outputjson --verifytypes".split()
MAX_ERROR_CHARS = 2_048


def main() -> None:
    sys.exit(Fixo().fix())


class Fixo:
    def fix(self) -> str | int:
        pyright = self.run((*_PYRIGHT, *self.args.files))

        return 0

    @cached_property
    def args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        help = "Files or directories to check (passed to pyright)"
        parser.add_argument("files", default="HEAD", nargs="?", help=help)

        help = "Immediately execute edits"
        parser.add_argument("-e", "--execute", action="store_true", help=help)

        help = "Command line for type checker"
        parser.add_argument("-t", "--type-check", default=_PYRIGHT, help=help)

        help = "Print more debug info"
        parser.add_argument("-v", "--verbose", action="store_true", help=help)

        return parser.parse_args()

    def run(self, cmd: str | Sequence[str], check: bool = True, **kwargs: Any) -> str:
        """Run a subprocess and return stdout as a string"""
        if self.args.verbose:
            print("$", *([cmd] if isinstance(cmd, str) else cmd))

        shell = kwargs.get("shell", False)
        if shell and not isinstance(cmd, str):
            cmd = shlex.join(cmd)
        elif not shell and isinstance(cmd, str):
            cmd = shlex.split(cmd)
        assert shell == isinstance(cmd, str)
        p = subprocess.run(cmd, text=True, capture_output=True, **kwargs)

        if self.args.verbose or (check and p.returncode):
            # TODO: Fix this output for lintrunner mode
            print(p.stdout[:MAX_ERROR_CHARS], file=sys.stderr)
            error = p.stderr if p.returncode else p.stderr[:MAX_ERROR_CHARS]
            print(error, file=sys.stderr)

        if check:
            p.check_returncode()

        return p.stdout


if __name__ == "__main__":
    main()
