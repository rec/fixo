import dataclasses as dc
from enum import Enum
from functools import cached_property


class Category(str, Enum):
    function = "function"
    param = "param"


@dc.dataclass
class LineCharacter:
    line: int
    character: int


@dc.dataclass(frozen=True)
class Message:
    # TODO: these fields are deliberately left underdefined, make better
    # ones once we have two examples
    name: str
    file: str
    severity: str
    message: str
    start: LineCharacter
    end: LineCharacter
    category: Category

    @cached_property
    def base_name(self) -> str:
        return self.name.rpartition(".")[2]
