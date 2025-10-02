from __future__ import annotations

import contextlib
import dataclasses as dc
import functools
import token
from itertools import groupby, takewhile
from tokenize import TokenInfo
from typing import Iterable, Iterator

from . import is_ignored


@dc.dataclass(frozen=True)
class Import:
    address: str
    as_: str
    line_number: int = 0  # REMOVE ME

    @staticmethod
    def create(token_line: Iterable[TokenInfo]) -> Iterator[Import]:
        # "from one.two import three as four, five"
        not_ignored = (t for t in token_line if not is_ignored(t.type))
        tokens = (t for t in not_ignored if t.string not in "()")
        if not ((tok := next(tokens, None)) and tok.string in ("import", "from")):
            return
        if tok.string == "from":
            non_imports = takewhile((lambda t: t.string != "import"), tokens)
            from_ = "".join(t.string for t in non_imports)
        else:
            from_ = ""

        # We're down to "three as four, five", so split by commas
        it = groupby(tokens, lambda t: t.string == ",")
        for parts in (p for k, g in it if not k and (p := [t.string for t in g])):
            as_index = next((i for i, p in enumerate(parts) if p == "as"), len(parts))
            imp = "".join(parts[:as_index])
            as_ = "".join(parts[as_index + 1 :])
            sep = "." if (from_ and imp and not from_.endswith(".")) else ""
            yield Import(
                address=from_ + sep + imp, as_=as_ or imp, line_number=tok.start[0]
            )
