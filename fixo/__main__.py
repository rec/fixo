from __future__ import annotations

import argparse
import contextlib
import dataclasses as dc
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from functools import cache, cached_property, partial, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Sequence, TypeVar, cast

from typing_extensions import TypeAlias

from . import rules, type_edit
from .tokens.python_file import PythonFile

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .message import Message


_PYRIGHT = 'pyright --ignoreexternal --outputjson --verifytypes'
MAX_ERROR_CHARS = 1024

_err = partial(print, file=sys.stderr)


class FixoError(Exception):
    pass


def main() -> None:
    try:
        Fixo().main()
    except FixoError as e:
        sys.exit('ERROR: ' + e.args[0])


class Fixo:
    def main(self) -> None:
        if not any(f.suffix == '.json' for f in self.args.files):
            self._find()
        elif len(self.args.files) == 1:
            self._execute()
        else:
            raise FixoError('Only only .json file is allowed')

    def _execute(self) -> None:
        (file,) = self.args.files
        data = json.loads(file.read_text())
        edits = {k: [type_edit.TypeEdit(**i) for i in v] for k, v in data.items()}
        self._edit(edits)

    def _find(self) -> None:
        rules = rules.make_rules(self.args.rule_set)
        if self.args.rules:
            if bad := ', '.join(r for r in self.args.rules if r not in rules):
                raise FixoError(f'Unknown --rule: {bad}')
            rules = {r: rules[r] for r in self.args.rules}

        tc = self.args.type_completeness
        if (p := Path(tc)).exists():
            assert p.suffix == '.json'
            pyright = p.read_text()
        else:
            pyright = self.run((*shlex.split(tc), *self.args.files))

        first_rule = next(iter(rules.values()))
        file_messages = first_rule.file_messages(pyright)
        edits = {k: list(v.edits(file_messages)) for k, v in rules.items()}

        if self.args.edit_immediately:
            self._edit(edits)
        else:
            edits_json = {k: [i.asdict() for i in v] for k, v in edits.items()}
            print(json.dumps(edits_json, indent=4))

    def _edit(self, edit_dict: dict[str, list[type_edit.TypeEdit]]) -> None:
        path_to_edits = {Path(k): v for k, v in edit_dict.items()}
        if nonexistent := [p for p in path_to_edits if not p.exists()]:
            raise FixoError(f'{nonexistent=}')
        for p, edits in path_to_edits.items():
            try:
                p.write_text(type_edit.perform_type_edits(edits, PythonFile(path=p)))
            except Exception as e:
                _err(f'ERROR: {p}:', *e.args)
                if self.args.verbose:
                    import traceback

                    traceback.print_exc()
            else:
                _err(f'{p}: {len(edits)}')

    @cached_property
    def args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        help = """If the files end in .json, they are edits to be executed, otherwise,
        they are a list of files or directories to be passed to pyright."""
        parser.add_argument('files', nargs='+', type=Path, help=help)

        help = "Immediately edit, don't write an edit file to be executed"
        parser.add_argument('-i', '--edit-immediately', action='store_true', help=help)

        help = 'Rules from the rule set to use'
        parser.add_argument('-r', '---rules', nargs='*', help=help)

        help = 'The rule set to use'
        parser.add_argument('-s', '---rule-set', type=str, default='', help=help)

        help = 'Command line or JSON file for type completeness'
        parser.add_argument('-t', '--type-completeness', default=_PYRIGHT, help=help)

        help = 'Print more debug info'
        parser.add_argument('-v', '--verbose', action='store_true', help=help)

        return parser.parse_args()

    def run(self, cmd: str | Sequence[str], check: bool = True, **kwargs: Any) -> str:
        """Run a subprocess and return stdout as a string"""
        if self.args.verbose:
            print('$', *([cmd] if isinstance(cmd, str) else cmd))

        shell = kwargs.get('shell', False)
        if shell and not isinstance(cmd, str):
            cmd = shlex.join(cmd)
        elif not shell and isinstance(cmd, str):
            cmd = shlex.split(cmd)
        assert shell == isinstance(cmd, str)
        p = subprocess.run(cmd, text=True, capture_output=True, **kwargs)

        if self.args.verbose or (check and p.returncode):
            # TODO: Fix this output for lintrunner mode
            print(p.stdout[:MAX_ERROR_CHARS], file=sys.stderr)
            error = p.stderr if p.returncode else p.stderr[:MAX_ERROR_CHARS]
            print(error, file=sys.stderr)

        if check:
            p.check_returncode()

        return p.stdout


if __name__ == '__main__':
    main()
