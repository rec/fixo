import abc
from tokenize import TokenInfo
from typing import Sequence

from . import data, io


@dc.dataclass
class TokenEdit:
    to_replace: slice
    replacement: Sequence[TokenInfo]

    def apply(self, tokens: list[TokenInfo]):
        tokens[self.to_replace] = self.replacement


@dc.dataclass
class Tokens:

    # Take from pytorch:/tools/linter/adaptors/_linter
    pass


class Edit(abc.ABC):
    pass


class Rule(abc.ABC):
    @abstractmethod
    def parse_into_messages(self, file: io.File) -> Iterator[data.Message]:
        ...

    @abstractmethod
    def accept_message(self, msg: data.Message) -> bool:
        ...
