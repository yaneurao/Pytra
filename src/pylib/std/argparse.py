"""Minimal pure-Python argparse subset for selfhost usage."""

from __future__ import annotations

from pylib.std import sys
from pylib.std.typing import Any


class Namespace:
    """Simple argparse.Namespace compatible container."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class _ArgSpec:
    def __init__(
        self,
        names: list[str],
        *,
        action: str | None,
        choices: list[str] | None,
        default: Any,
        help_text: str | None,
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

    def __init__(self, description: str | None = None) -> None:
        self.description = description or ""
        self._specs: list[_ArgSpec] = []

    def add_argument(
        self,
        *names: str,
        help: str | None = None,
        action: str | None = None,
        choices: list[str] | None = None,
        default: Any = None,
    ) -> None:
        if len(names) == 0:
            raise ValueError("add_argument requires at least one name")
        spec = _ArgSpec(list(names), action=action, choices=choices, default=default, help_text=help)
        self._specs.append(spec)

    def _fail(self, msg: str) -> None:
        if msg != "":
            sys.write_stderr(f"error: {msg}\n")
        raise SystemExit(2)

    def parse_args(self, argv: list[str] | None = None) -> Namespace:
        args = list(sys.argv[1:] if argv is None else argv)

        specs_pos = [s for s in self._specs if not s.is_optional]
        specs_opt = [s for s in self._specs if s.is_optional]
        by_name: dict[str, _ArgSpec] = {}
        for s in specs_opt:
            for n in s.names:
                by_name[n] = s

        values: dict[str, Any] = {}
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
            tok = args[i]
            if tok.startswith("-"):
                spec = by_name.get(tok)
                if spec is None:
                    self._fail(f"unknown option: {tok}")
                if spec.action == "store_true":
                    values[spec.dest] = True
                    i += 1
                    continue
                if i + 1 >= len(args):
                    self._fail(f"missing value for option: {tok}")
                val = args[i + 1]
                if spec.choices is not None and val not in spec.choices:
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

        return Namespace(**values)

