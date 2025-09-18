import pytest

from fixo.tokens.import_line import ImportLine

TESTS = (
    ("import math  # An import", "", [("math", "")]),
    ("import a.c", "", [("a.c", "")]),
    ("from pathlib import Path", "pathlib", [("Path", "")]),
    ("from . import x", ".", [("x", "")]),
    ("from .x.z import y", ".x.z", [("y", "")]),
    ("from a.b import c", "a.b", [("c", "")]),
    ("from a import c as d", "a", [("c", "d")]),
    ("import math as moth", "", [("math", "moth")]),
    ("from m import sin as s, cos as c  #, a as b", "m", [("sin", "s"), ("cos", "c")]),
    ("import math as m  , math as t", "", [("math", "m"), ("math", "t")]),
    ("from x . y . z import w", "x.y.z", [("w", "")]),
)


@pytest.mark.parametrize("line, from_, imports", TESTS)
def test_import_line(line, from_, imports):
    imp = ImportLine.create(line)
    assert imp.from_ == from_ and imp.imports == imports
