from tokenize import generate_tokens

from fixo.token_edit import TokenEdit, perform_edits

SOURCE = """

# A comment
class Top:
    def is_cool(self, tensor):
        return True


"""
EXPECTED = """

# A comment
class Top:
    def is_cool(self, tensor: Tensor) -> bool:
        return True


"""


def test_edit():
    tokens = list(generate_tokens(iter(SOURCE.splitlines(keepends=True)).__next__))
    assert tokens[14].string == "tensor"
    assert tokens[16].string == ":"

    edits = TokenEdit(16, " -> bool"), TokenEdit(15, ": Tensor")
    actual = perform_edits(edits, tokens)
    assert actual == EXPECTED
