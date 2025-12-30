from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from collections.abc import Sequence
from functools import cache, cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import type_edit
from .blocks.python_file import PythonFile
from .rules import make_rules

if TYPE_CHECKING:
    from .rule import Rule


MAX_ERROR_CHARS = 1024

_err = partial(print, file=sys.stderr)


@cache
def args() -> Namespace:
    parser = argparse.ArgumentParser()
    add = parser.add_argument

    help = """If the files end in .json, they are edits to be executed, otherwise,
    they are a list of files or directories to be passed to the type checker."""
    add("files", nargs="+", type=Path, help=help)

    help = "Immediately edit, don't write an edit file to be executed"
    add("-i", "--edit-immediately", action="store_true", help=help)

    help = "Command line or JSON file for type completeness"
    add("-c", "--type-completeness", type=str, default="", help=help)

    help = "Rules from the rule set to use"
    add("-r", "--rules", nargs="*", help=help)

    help = "The rule set to use"
    add("-s", "--rule-set", type=str, default="", help=help)

    help = "Which type checker to use?"
    add("-t", "--type-checker", default="pyright", help=help)

    help = "Print more debug info"
    add("-v", "--verbose", action="store_true", help=help)

    return parser.parse_args()


class FixoError(Exception):
    pass


def main() -> None:
    try:
        Fixo().main()
    except FixoError as e:
        sys.exit("ERROR: " + e.args[0])


class Fixo:
    def main(self) -> None:
        if not any(f.suffix == ".json" for f in args().files):
            self._find()
        elif len(args().files) == 1:
            self._execute()
        else:
            raise FixoError("Only only .json file is allowed")

    @cached_property
    def rules(self) -> dict[str, Rule]:
        rules = make_rules(args().rule_set)
        if not args().rules:
            return rules

        if bad := ", ".join(r for r in args().rules if r not in rules):
            raise FixoError(f"Unknown --rule: {bad}")

        return {r: rules[r] for r in args().rules}

    def _execute(self) -> None:
        (file,) = args().files
        data = json.loads(file.read_text())
        edits = {k: [type_edit.TypeEdit(**i) for i in v] for k, v in data.items()}
        self._edit(edits)

    def _find(self) -> None:
        tc = args().type_completeness  # or

        if (p := Path(tc)).exists() and p.suffix == ".json":
            results = p.read_text()
        else:
            results = self.run((*shlex.split(tc), *args().files))

        first_rule = next(iter(self.rules.values()))
        file_messages = first_rule.file_messages(results)
        edits = {k: list(v.edits(file_messages)) for k, v in self.rules.items()}

        if args().edit_immediately:
            self._edit(edits)
        else:
            edits_json = {k: [i.asdict() for i in v] for k, v in edits.items()}
            print(json.dumps(edits_json, indent=4))

    def _edit(self, edit_dict: dict[str, list[type_edit.TypeEdit]]) -> None:
        path_to_edits = {Path(k): v for k, v in edit_dict.items()}
        if nonexistent := [p for p in path_to_edits if not p.exists()]:
            raise FixoError(f"{nonexistent=}")
        for p, edits in path_to_edits.items():
            try:
                p.write_text(type_edit.perform_type_edits(edits, PythonFile(path=p)))
            except Exception as e:
                _err(f"ERROR: {p}:", *e.args)
                if args().verbose:
                    import traceback

                    traceback.print_exc()
            else:
                _err(f"{p}: {len(edits)}")

    def run(self, cmd: str | Sequence[str], check: bool = True, **kwargs: Any) -> str:
        """Run a subprocess and return stdout as a string"""
        if args().verbose:
            print("$", *([cmd] if isinstance(cmd, str) else cmd))

        shell = kwargs.get("shell", False)
        if shell and not isinstance(cmd, str):
            cmd = shlex.join(cmd)
        elif not shell and isinstance(cmd, str):
            cmd = shlex.split(cmd)
        assert shell == isinstance(cmd, str)
        p = subprocess.run(cmd, text=True, capture_output=True, **kwargs)

        if args().verbose or (check and p.returncode):
            # TODO: Fix this output for lintrunner mode
            print(p.stdout[:MAX_ERROR_CHARS], file=sys.stderr)
            error = p.stderr if p.returncode else p.stderr[:MAX_ERROR_CHARS]
            print(error, file=sys.stderr)

        if check:
            p.check_returncode()

        return p.stdout


if __name__ == "__main__":
    main()
