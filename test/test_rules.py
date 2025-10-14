import json
import os
from pathlib import Path
from typing import Protocol

from fixo.edits import perform_type_edits, TypeEdit
from fixo.rule import Rule
from fixo.tokens.python_file import PythonFile

RULES_DATA = Path(__file__).parent / "rules.json"
REPORT = Path(__file__).parent / "sample_code.pyright.json"
SAMPLE_IN = Path(__file__).parent / "sample_code.py"
SAMPLE_OUT = Path(__file__).parent / "sample_code.out.py"
REWRITE_EXPECTED = os.environ.get("REWRITE_EXPECTED")


def test_messages():
    rules = Rule.read_all(RULES_DATA)
    parsers = dict.fromkeys(rule.parse_into_messages for rule in rules.values())
    assert len(parsers) == 1, parsers
    msgs = list(parsers.popitem()[0](REPORT))
    assert len(msgs) == 6

    rmsgs = {k: [m for m in msgs if r.accept_message(m, r)] for k, r in rules.items()}
    lengths = [len(m) for m in rmsgs.values()]

    assert lengths == [2, 1], msgs


def test_run_rules():
    edits = {k: list(v.run(REPORT)) for k, v in Rule.read_all(RULES_DATA).items()}
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
        TypeEdit(function_name="four", type_name="torch.Tensor", param="self"),
    ],
}
