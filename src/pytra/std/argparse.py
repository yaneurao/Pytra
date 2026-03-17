"""Minimal pure-Python argparse subset for selfhost usage."""

from __future__ import annotations

from pytra.std import sys


class Namespace:
    """Simple argparse.Namespace compatible container."""

    values: dict[str, str | bool | None]

    def __init__(self, values: dict[str, str | bool | None] | None = None) -> None:
        if values is None:
            self.values = {}
            return
        self.values = values


class _ArgSpec:
    names: list[str]
    action: str
    choices: list[str]
    default: str | bool | None
    help_text: str
    is_optional: bool
    dest: str

    def __init__(
        self,
        names: list[str],
        *,
        action: str = "",
        choices: list[str] = [],
        default: str | bool | None = None,
        help_text: str = "",
    ) -> None:
        self.names = names
        self.action = action
        self.choices = choices
        self.default = default
        self.help_text = help_text
        self.is_optional = len(names) > 0 and names[0].startswith("-")
        if self.is_optional:
            base = names[-1].lstrip("-").replace("-", "_")
            self.dest = base
        else:
            self.dest = names[0]


class ArgumentParser:
    """Subset of argparse.ArgumentParser used by this repository."""

    description: str
    _specs: list[_ArgSpec]

    def __init__(self, description: str = "") -> None:
        self.description = description
        self._specs: list[_ArgSpec] = []

    def add_argument(
        self,
        name0: str,
        name1: str = "",
        name2: str = "",
        name3: str = "",
        help: str = "",
        action: str = "",
        choices: list[str] = [],
        default: str | bool | None = None,
    ) -> None:
        names: list[str] = []
        if name0 != "":
            names.append(name0)
        if name1 != "":
            names.append(name1)
        if name2 != "":
            names.append(name2)
        if name3 != "":
            names.append(name3)
        if len(names) == 0:
            raise ValueError("add_argument requires at least one name")
        spec = _ArgSpec(names, action=action, choices=choices, default=default, help_text=help)
        self._specs.append(spec)

    def _fail(self, msg: str) -> None:
        if msg != "":
            sys.write_stderr(f"error: {msg}\n")
        raise SystemExit(2)

    def parse_args(self, argv: list[str] | None = None) -> dict[str, str | bool | None]:
        args: list[str]
        if argv is None:
            args = sys.argv[1:]
        else:
            args = list(argv)

        specs_pos: list[_ArgSpec] = []
        specs_opt: list[_ArgSpec] = []
        for s in self._specs:
            if s.is_optional:
                specs_opt.append(s)
            else:
                specs_pos.append(s)
        by_name: dict[str, int64] = {}
        spec_i = 0
        for s in specs_opt:
            for n in s.names:
                by_name[n] = spec_i
            spec_i += 1

        values: dict[str, str | bool | None] = {}
        for s in self._specs:
            if s.action == "store_true":
                values[s.dest] = bool(s.default) if s.default is not None else False
            elif s.default is not None:
                values[s.dest] = s.default
            else:
                values[s.dest] = None

        pos_i = 0
        i = 0
        while i < len(args):
            tok: str = args[i]
            if tok.startswith("-"):
                if tok not in by_name:
                    self._fail(f"unknown option: {tok}")
                spec = specs_opt[by_name[tok]]
                if spec.action == "store_true":
                    values[spec.dest] = True
                    i += 1
                    continue
                if i + 1 >= len(args):
                    self._fail(f"missing value for option: {tok}")
                val: str = args[i + 1]
                if len(spec.choices) > 0 and val not in spec.choices:
                    self._fail(f"invalid choice for {tok}: {val}")
                values[spec.dest] = val
                i += 2
                continue

            if pos_i >= len(specs_pos):
                self._fail(f"unexpected extra argument: {tok}")
            spec = specs_pos[pos_i]
            values[spec.dest] = tok
            pos_i += 1
            i += 1

        if pos_i < len(specs_pos):
            self._fail(f"missing required argument: {specs_pos[pos_i].dest}")

        return values
