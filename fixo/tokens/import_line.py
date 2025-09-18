from __future__ import annotations

import dataclasses as dc


@dc.dataclass
class ImportLine:
    from_: str
    imports: list[tuple[str, str]]

    def addresses(self) -> list[str]:
        from_ = self.from_ + "." if self.from_ else ""
        return [from_ + a for a, _ in self.imports]

    @staticmethod
    def create(line: str) -> ImportLine:
        def despace(s: str) -> str:
            return s.replace(" ", "")

        line = line.partition("#")[0].strip()
        from_, _, import_ = line.partition(" import ")

        if import_:
            empty, _, f = from_.partition("from ")
            assert f and not empty, (f, empty, line)
            from_ = despace(f)
        else:
            from_, _, import_ = line.partition("import ")
            assert not from_
        as_clauses = [i.partition(" as ")[::2] for i in import_.split(",")]
        return ImportLine(from_, [(despace(a), despace(b)) for a, b in as_clauses])
