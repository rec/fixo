import json
from pathlib import Path
from typing import Protocol

from fixo.rule import Rule

DATA = Path(__file__).parent / "rules.json"
REPORT = Path(__file__).parent / "full-out.json"


def test_simple_rule_from_data():
    Rule.create(parent=".pyright")


def test_rules_from_file():
    rule_data = json.loads(DATA.read_text())

    rules = [Rule.create(**r) for r in rule_data.values()]
    report = json.loads(REPORT.read_text())
