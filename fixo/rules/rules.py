import json
from functools import cache
from pathlib import Path
from typing import Any

from ..rule import Rule


def create_all(d: dict[str, Any], parent: str = "") -> dict[str, Rule]:
    return {k: Rule.create(parent=parent, **v) for k, v in d.items()}


def make_rules(s: str, parent: str = "") -> dict[str, Rule]:
    if s:
        d = json.loads(s if "{" in s else Path(s).read_text())
        assert isinstance(d, dict), (s, d)
    else:
        d = _RULE_DATA

    return create_all(d, parent=parent)


@cache
def default_rules(parent: str = "") -> dict[str, Rule]:
    return create_all(_RULE_DATA, parent)


_RULE_DATA = {
    "bools": {
        # "parent": ".pyright",
        "name_match": "(is|has)_.*",
        "type_name": "bool",
    },
    "self_params": {
        # "parent": ".pyright",
        "categories": ["function"],
        "name_match": "self",
        "type_name": "torch.Tensor",
    },
}
