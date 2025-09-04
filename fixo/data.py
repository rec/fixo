import dataclasses as dc


@dc.dataclass
class LineCharacter:
    line: int
    character: int


@dc.dataclass
class Message:
    source_name: str
    file: str
    severity: str
    message: str
    start: LineCharacter
    end: LineCharacter
