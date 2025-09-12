from typing import Protocol

from fixo.rule import Rule


def test_simple_rule_from_data():
    Rule.create(parent=".pyright")
