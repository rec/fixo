"""
Some features in this program are implemented with callable class members which are
imported at run time by name, rather than an abstract method, so these members can be
customized by the user with their own code.
"""

import importlib
from typing import Any, Generic, TypeVar, get_args

_T = TypeVar("_T")

BASE_ADDRESS = "fixo.rules"


class Loader(Generic[_T]):
    def __init__(self):
        self._T = get_args(getattr(self, "__orig_class__", None))[0]

    def __call__(self, address: Any) -> _T:
        if isinstance(address, str):
            data = import_symbol(address)
        else:
            data = address
        if isinstance(data, self._T):
            return data
        raise TypeError(f"Expected type {self._T} but at {address=}, got {data=}")


def import_symbol(address: str) -> Any:
    if address.startswith("."):
        address = BASE_ADDRESS + address
    module, _, name = address.rpartition(".")
    return getattr(importlib.import_module(module), name)
