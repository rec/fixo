from __future__ import annotations

import contextlib
import dataclasses as dc
import functools
import token
from itertools import groupby, takewhile
from tokenize import TokenInfo
from typing import Iterable, Iterator


@dc.dataclass(frozen=True)
class Import:
    address: str
    as_: str

    def create(token_line: Iterable[TokenInfo]) -> Iterator[Import]:
        # "from one.two import three as four, five"
        is_terminal = (token.ENDMARKER, token.INDENT, token.NL).__contains__
        is_ignored = (token.INDENT, token.COMMENT).__contains__

        until_terminal = takewhile((lambda t: not is_terminal(t.type)), token_line)
        not_ignored = (t for t in until_terminal if not is_ignored(t.type))
        tokens = (t for t in not_ignored if t.string not in "()")
        if not ((tok := next(tokens, None)) and tok.string in ("import", "from")):
            return
        if tok.string == "from":
            from_ = "".join(takewhile((lambda t: t.string != "import"), tokens))  # type: ignore[attr-defined, arg-type]
        else:
            from_ = ""

        # We're down to "three as four, five", so split by commas
        it = groupby(tokens, lambda t: t.string == ",")
        for parts in (p for k, g in it if not k and (p := [t.string for t in g])):
            as_index = next((i for i, p in enumerate(parts) if p == "as"), len(parts))
            imp = "".join(parts[:as_index])
            as_ = "".join(parts[as_index + 1 :])
            sep = "." if (from_ and imp and not from_.endswith(".")) else ""
            yield Import(address=from_ + sep + imp, as_=as_ or imp)
