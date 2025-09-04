import abc
from tokenize import TokenInfo
from typing import Sequence

from . import data, io
from . tokens import PythonFile

from enum import Enum


@dc.dataclass
class TokenEdit:
    """Represents an edit as changes to tokens in a token file"""
    to_replace: slice
    replacement: Sequence[TokenInfo]

    def apply(self, tokens: list[TokenInfo]):
        tokens[self.to_replace] = self.replacement


@dc.dataclass
class Edit(abc.ABC):
    address: str

    @abstractmethod
    def edit_to_token_edits(self, pf: PythonFile) -> Iterator[TokenEdit]: ...


class Rule(abc.ABC):
    @abstractmethod
    def parse_into_messages(self, file: io.File) -> Iterator[data.Message]: ...

    @abstractmethod
    def accept_message(self, msg: data.Message) -> bool: ...

    @abstractmethod
    def message_to_edits(self, pf: PythonFile, msg: data.Message) -> Iterator[Edit]: ...
