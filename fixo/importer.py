"""
Some features in this program are implemented with callable class members which are
imported at run time by name, rather than an abstract method, so these members can be
customized by the user with their own code.
"""

import dataclasses as dc
import importlib
from typing import TYPE_CHECKING, Any, Generic, TypeVar, get_args

_T = TypeVar("_T")

BASE_ADDRESS = "fixo.rules"


class Importer(Generic[_T]):
    def __call__(self, prefix: str, address: Any) -> _T:
        if isinstance(address, str):
            if address.startswith("."):
                address = prefix + address
            data = import_symbol(address)
        else:
            data = address
        T = get_args(getattr(self, "__orig_class__", None))[0]
        if isinstance(data, T):
            return data
        raise TypeError(f"Expected type {T} but at {address=}, got {data=}")


def import_symbol(address: str) -> Any:
    if address.startswith("."):
        address = BASE_ADDRESS + address
    try:
        return importlib.import_module(address)
    except ImportError:
        pass
    module, _, name = address.rpartition(".")
    return getattr(importlib.import_module(module), name)


def import_dict(address: str) -> dict[str, Any]:
    x = import_symbol(address)
    if callable(x):
        x = x()
    if isinstance(x, dict):
        return x
    elif dc.is_dataclass(x):
        return dc.asdict(x)  # type: ignore[arg-type]
    else:
        return {k: v for k, v in vars(x).items() if not k.startswith("_")}
