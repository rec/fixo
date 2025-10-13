import json
from pathlib import Path
from typing import Protocol

from fixo.edits import TypeEdit
from fixo.rule import Rule

RULES_DATA = Path(__file__).parent / "rules.json"
REPORT = Path(__file__).parent / "sample_code.pyright.json"

EXPECTED_EDITS = {
    "bools": [
        TypeEdit(function_name="A", type_name="bool", param="is_nice"),
        TypeEdit(function_name="A.one", type_name="bool", param=""),
        TypeEdit(function_name="A.is_two", type_name="bool", param="self"),
    ],
    "self_params": [
        TypeEdit(function_name="A.is_two", type_name="torch.Tensor", param="self"),
    ],
}


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
