from typing import NamedTuple

import pytest

from fixo.tokens.import_line import ImportLine

SPLIT_TESTS = (
    ("import math  # An import", "", [("math", "")], ["math"]),
    ("import a.c", "", [("a.c", "")], ["a.c"]),
    ("from pathlib import Path", "pathlib", [("Path", "")], ["pathlib.Path"]),
    ("from . import x", ".", [("x", "")], [".x"]),
    ("from .x.z import y", ".x.z", [("y", "")], [".x.z.y"]),
    ("from a.b import c", "a.b", [("c", "")], ["a.b.c"]),
    ("from a import c as d", "a", [("c", "d")], ["a.c"]),
    ("import math as moth", "", [("math", "moth")], ["math"]),
    (
        "from m import sin as s, cos as c  #, a as b",
        "m",
        [("sin", "s"), ("cos", "c")],
        ["m.sin", "m.cos"],
    ),
    (
        "import math as m  , math as t",
        "",
        [("math", "m"), ("math", "t")],
        ["math", "math"],
    ),
    ("from x . y . z import w", "x.y.z", [("w", "")], ["x.y.z.w"]),
)


@pytest.mark.parametrize("line, from_, imports, addresses", SPLIT_TESTS)
def test_import_line_split(line, from_, imports, addresses):
    imp = ImportLine.create(line, 1)
    assert imp.from_ == from_
    assert imp.imports == imports
    assert imp.addresses() == addresses


ADDRESS_TESTS = (
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
