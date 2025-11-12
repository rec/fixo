import itertools
import token
from tokenize import TokenInfo, generate_tokens
from typing import NamedTuple

import pytest

from fixo.tokens.imports import Import


def _to_token_lines(s: str) -> list[list[TokenInfo]]:
    it = list(generate_tokens(iter(s.splitlines(keepends=True)).__next__))
    line_it = itertools.groupby(it, lambda t: t.type == token.NEWLINE)
    return [list(g) for k, g in line_it if not k]


def test_import_line():
    token_lines = _to_token_lines(SOURCE)
    actual = [i for tl in token_lines for i in Import.create(tl)]
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
    Import(address='math', as_='math', line_number=2),
    Import(address='a.c', as_='a.c', line_number=3),
    Import(address='pathlib.Path', as_='Path', line_number=4),
    Import(address='.x', as_='x', line_number=5),
    Import(address='.x.z.y', as_='y', line_number=6),
    Import(address='a.b.c', as_='c', line_number=7),
    Import(address='a.c', as_='d', line_number=8),
    Import(address='math', as_='moth', line_number=9),
    Import(address='x.y.z.w', as_='w', line_number=10),
    Import(address='m.sin', as_='s', line_number=11),
    Import(address='m.cos', as_='c', line_number=11),
    Import(address='math', as_='m', line_number=12),
    Import(address='math', as_='t', line_number=12),
    Import(address='torch.Tensor', as_='Mensor', line_number=15),
    Import(address='torch.dtype', as_='mtype', line_number=15),
]
