import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import pytest

from fixo.blocks.python_file import PythonFile
from fixo.rules import default_rules
from fixo.type_edit import TypeEdit, perform_type_edits

SAMPLE_IN = Path(__file__).parent / "sample_code.py"
SAMPLE_OUT = Path(__file__).parent / "sample_code.out.py"
REWRITE_EXPECTED = os.environ.get("REWRITE_EXPECTED")


@dataclass
class TypeChecker:
    name: str
    report_path: Path
    message_count: int
    lengths: list[int]

    def __repr__(self):
        return f"{self.name.capitalize()}TypeChecker"

    @staticmethod
    def make(name, message_count, lengths):
        report_path = Path(__file__).parent / f"sample_code.{name}.json"
        return TypeChecker(name, report_path, message_count, lengths)

    @cached_property
    def parent(self) -> str:
        return f".{self.name}"

    @cached_property
    def report(self) -> str:
        return self.report_path.read_text()

    @cached_property
    def rules(self):
        return default_rules(self.parent)


TYPE_CHECKERS = [TypeChecker.make("pyright", 6, [2, 1])]
PYREFLY = [TypeChecker.make("pyrefly", 5, [5, 5])]


@pytest.mark.parametrize("type_checker", PYREFLY + TYPE_CHECKERS)
def test_messages(type_checker):
    rules = type_checker.rules.values()
    parsers = dict.fromkeys(rule.parse_into_messages for rule in rules)
    msgs = list(parsers.popitem()[0](type_checker.report))
    assert len(msgs) == type_checker.message_count, (msgs, type_checker)
    assert not parsers, parsers

    items = default_rules(type_checker.parent).items()
    rmsgs = {k: [m for m in msgs if r.accept_message(m, r)] for k, r in items}
    lengths = [len(m) for m in rmsgs.values()]

    assert lengths == type_checker.lengths, msgs


@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_run_rules(type_checker):
    t = type_checker.report
    items = type_checker.rules.items()
    edits = {k: list(v.edits(v.file_messages(t))) for k, v in items}
    assert edits == EXPECTED_EDITS

    pf = PythonFile(path=SAMPLE_IN)
    result = perform_type_edits((i for e in edits.values() for i in e), pf)
    if REWRITE_EXPECTED or not SAMPLE_OUT.exists():
        SAMPLE_OUT.write_text(result)
    else:
        assert SAMPLE_OUT.read_text() == result


EXPECTED_EDITS = {
    "bools": [
        TypeEdit(function_name="A.one", type_name="bool", param="is_nice"),
        TypeEdit(function_name="A.is_two", type_name="bool", param=""),
    ],
    "self_params": [
        TypeEdit(function_name="three", type_name="torch.Tensor", param="self"),
    ],
}
