from __future__ import annotations

import contextlib
import dataclasses as dc
import functools
import token
from itertools import groupby
from tokenize import TokenInfo
from typing import Iterator


@dc.dataclass(frozen=True)
class Import:
    address: str
    as_: str

    def create(token_line: Iterator[TokenInfo]) -> Iterator[Import]:
        # "from one.two import three as four, five"
        with contextlib.suppress(StopIteration):
            ignored = {token.INDENT, token.NL, token.COMMENT}
            it = (t for t in token_line if not (t.type in ignored or t.string in "()"))

            if (t := next(it)).string not in ("import", "from"):
                return

            if t.string == "import":
                from_ = ""
            else:
                from_tokens = []
                while (t := next(it)).string != "import":
                    from_tokens.append(t.string)
                from_ = "".join(from_tokens)

            # We're down to "three as four, five"
            for k, g in groupby(it, lambda t: t.string == ","):
                if not k and (parts := [t.string for t in g]):
                    try:
                        as_index = parts.index("as")
                    except ValueError:
                        as_ = ""
                    else:
                        as_ = "".join(parts[as_index + 1 :])
                        parts = parts[:as_index]

                    sep = "." if (from_ and parts and not from_.endswith(".")) else ""
                    imp = "".join(parts)
                    yield Import(address=from_ + sep + imp, as_=as_ or imp)
