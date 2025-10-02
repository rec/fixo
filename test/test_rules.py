import json
from pathlib import Path
from typing import Protocol

from fixo.rule import Rule

RULES_DATA = Path(__file__).parent / "rules.json"
REPORT = Path(__file__).parent / "sample_code.pyright.json"


def test_simple_rule_from_data():
    Rule.create(parent=".pyright")


def test_messages():
    rules = Rule.read(RULES_DATA)
    parsers = dict.fromkeys(rule.parse_into_messages for rule in rules.values())
    assert len(parsers) == 1, parsers
    messages = list(parsers.popitem()[0](REPORT))
    assert len(messages) == 5
    for k, v in rules.items():
        pass
