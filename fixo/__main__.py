from __future__ import annotations

import argparse
import contextlib
import dataclasses as dc
import json
import re
import subprocess
import sys
from collections import Counter
from functools import cache, cached_property, partial, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Sequence, TypeVar, cast

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterable


def main() -> None:
    sys.exit(Fixo().fix())


class Fixo:
    def fix(self) -> str | int:
        return 0

    @cached_property
    def args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        help = "Files or directories to check (passed to pyright)"
        parser.add_argument("files", default="HEAD", nargs="?", help=help)

        help = "Immediately execute edits"
        parser.add_argument("-e", "--execute", action="store_true", help=help)

        return parser.parse_args()


if __name__ == "__main__":
    main()
