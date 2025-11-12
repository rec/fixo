import json
from functools import cache
from pathlib import Path

from ..rule import Rule


def make_rules(s: str) -> dict[str, Rule]:
    return Rule.create_all(
        json.loads(s if '{' in s else Path(s).read_text()) if s else _RULE_DATA
    )


@cache
def default_rules() -> dict[str, Rule]:
    return Rule.create_all(_RULE_DATA)


_RULE_DATA = {
    'bools': {'parent': '.pyright', 'name_match': '(is|has)_.*', 'type_name': 'bool'},
    'self_params': {
        'parent': '.pyright',
        'categories': ['function'],
        'name_match': 'self',
        'type_name': 'torch.Tensor',
    },
}
