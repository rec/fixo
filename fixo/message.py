import dataclasses as dc
import typing as t
from functools import cached_property


@dc.dataclass
class LineCharacter:
    line: int
    character: int


@dc.dataclass(frozen=True)
class Message:
    source_name: str
    file: str
    severity: str
    message: str
    start: LineCharacter
    end: LineCharacter
    category: str

    @cached_property
    def base_name(self) -> str:
        return self.source_name.rpartition(".")[2]
