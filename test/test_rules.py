import json
import os
from pathlib import Path
from typing import Protocol

from fixo.blocks.python_file import PythonFile
from fixo.rule import Rule
from fixo.rules import default_rules
from fixo.type_edit import TypeEdit, perform_type_edits

REPORT = Path(__file__).parent / "sample_code.pyright.json"
SAMPLE_IN = Path(__file__).parent / "sample_code.py"
SAMPLE_OUT = Path(__file__).parent / "sample_code.out.py"
REWRITE_EXPECTED = os.environ.get("REWRITE_EXPECTED")


def test_messages():
    parsers = dict.fromkeys(
        rule.parse_into_messages for rule in default_rules().values()
    )
    assert len(parsers) == 1, parsers
    msgs = list(parsers.popitem()[0](REPORT.read_text()))
    assert len(msgs) == 6

    rmsgs = {
        k: [m for m in msgs if r.accept_message(m, r)]
        for k, r in default_rules().items()
    }
    lengths = [len(m) for m in rmsgs.values()]

    assert lengths == [2, 1], msgs


def test_run_rules():
    t = REPORT.read_text()
    edits = {k: list(v.edits(v.file_messages(t))) for k, v in default_rules().items()}
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
