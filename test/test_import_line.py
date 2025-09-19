from typing import NamedTuple
from tokenize import TokenInfo, generate_tokens
import itertools
import token

import pytest

from fixo.tokens.import_line import Import

def _to_token_lines(s: str) -> list[list[TokenInfo]]:
    it = list(generate_tokens(iter(s.splitlines(keepends=True)).__next__))
    line_it = itertools.groupby(it, lambda t: t.type == token.NEWLINE)
    return [list(g) for k, g in line_it if not k]


def test_import_line():
    token_lines = _to_token_lines(SOURCE)
    actual = [i for tl in token_lines for i in Import.create(tl)]
    print(*actual, sep="\n")
    assert actual == EXPECTED


SOURCE = """
import math  # An import
import a.c
from pathlib import Path
from . import x
from .x.z import y
from a.b import c
from a import c as d
import math as moth
from x . y . z import w
from m import sin as s, cos as c  #, a as b
import math as m  , math as t

#
from torch import (
  Tensor as Mensor,
  dtype as mtype,
)
"""

EXPECTED = [
    Import(address='math', as_='math'),
    Import(address='a.c', as_='a.c'),
    Import(address='pathlib.Path', as_='Path'),
    Import(address='.x', as_='x'),
    Import(address='.x.z.y', as_='y'),
    Import(address='a.b.c', as_='c'),
    Import(address='a.c', as_='d'),
    Import(address='math', as_='moth'),
    Import(address='x.y.z.w', as_='w'),
    Import(address='m.sin', as_='s'),
    Import(address='m.cos', as_='c'),
    Import(address='math', as_='m'),
    Import(address='math', as_='t'),
    Import(address='torch.Tensor', as_='Mensor'),
    Import(address='torch.dtype', as_='mtype'),
    ##!
]
