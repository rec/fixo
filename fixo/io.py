import json
from io import TextIOWrapper
from pathlib import Path
from typing import Any, TypeAlias

File: TypeAlias = str | Path | TextIOWrapper


def read_json(file: File) -> dict[str, Any]:
    if isinstance(file, TextIOWrapper):
        return json.load(file)
    else:
        with open(file) as fp:
            return json.load(fp)
