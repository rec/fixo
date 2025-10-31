from functools import cache

from ..rule import Rule


@cache
def default_rules() -> dict[str, Rule]:
    return Rule.create_all(_RULE_DATA)


_RULE_DATA = {
    "bools": {"parent": ".pyright", "name_match": "(is|has)_.*", "type_name": "bool"},
    "self_params": {
        "parent": ".pyright",
        "categories": ["function"],
        "name_match": "self",
        "type_name": "torch.Tensor",
    },
}
