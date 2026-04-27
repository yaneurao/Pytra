from __future__ import annotations

import json
import sys
import unittest
import typing as py_typing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pytest
except ImportError:  # pragma: no cover - exercised in minimal local envs.
    pytest = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.std import argparse as py_argparse
from src.pytra.std import re as py_re
from src.pytra.std import sys as py_sys
from src.pytra.enum import Enum, IntEnum, IntFlag


CASE_ROOT = ROOT / "test" / "cases" / "pylib"
_MISSING = object()


@dataclass
class Point:
    x: int
    y: int = 0


@dataclass
class MyError(Exception):
    category: str
    summary: str


class Color(Enum):
    RED = 1
    BLUE = 2


class Status(IntEnum):
    OK = 0
    ERROR = 1


class Perm(IntFlag):
    READ = 1
    WRITE = 2
    EXEC = 4


def _case_paths() -> list[Path]:
    if not CASE_ROOT.exists():
        return []
    return sorted(CASE_ROOT.rglob("*.json"))


def _case_id(path: Path) -> str:
    return path.relative_to(CASE_ROOT).with_suffix("").as_posix()


def _load_case(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)
    if not isinstance(case, dict):
        raise AssertionError(f"{path}: case root must be an object")
    return case


def _run_named_case(name: str) -> dict[str, Any]:
    if name == "argparse_positional_option":
        p = py_argparse.ArgumentParser("x")
        p.add_argument("input")
        p.add_argument("-o", "--output")
        p.add_argument("--pretty", action="store_true")
        return p.parse_args(["a.py", "-o", "out.cpp", "--pretty"])
    if name == "argparse_choices":
        p = py_argparse.ArgumentParser("x")
        p.add_argument("input")
        p.add_argument("--mode", choices=["a", "b"], default="a")
        return p.parse_args(["in.py", "--mode", "b"])
    if name == "dataclasses_init_defaults":
        p = Point(1)
        return {"x": p.x, "y": p.y}
    if name == "dataclasses_repr_eq":
        a = Point(1, 2)
        b = Point(1, 2)
        c = Point(2, 1)
        return {"repr": repr(a), "a_eq_b": a == b, "a_eq_c": a == c}
    if name == "dataclasses_exception_subclass":
        e = MyError("kind", "message")
        return {"category": e.category, "summary": e.summary}
    if name == "enum_basic":
        return {"red_eq_red": Color.RED == Color.RED, "red_eq_blue": Color.RED == Color.BLUE}
    if name == "intenum_basic":
        return {"ok_eq_zero": Status.OK == 0, "error_int": int(Status.ERROR)}
    if name == "intflag_bitops":
        rw = Perm.READ | Perm.WRITE
        return {
            "rw": int(rw),
            "rw_and_write": int(rw & Perm.WRITE),
            "rw_xor_write": int(rw ^ Perm.WRITE),
        }
    if name == "re_match_basic":
        m = py_re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", "x = 1")
        if m is None:
            return {"group1": None, "group2": None}
        return {"group1": m.group(1), "group2": m.group(2)}
    if name == "re_sub_ws":
        return {"out": py_re.sub(r"\s+", " ", "a\nb\tc")}
    if name == "re_import_regex":
        return {
            "import_os_matches": py_re.match(r"^import\s+(.+)$", "import os") is not None,
            "import_modules_matches": py_re.match(
                r"^import\s+(.+)$", "import_modules: dict[str, str] = {}"
            )
            is not None,
        }
    if name == "sys_wrapper_exports":
        return {
            "argv_is_list": isinstance(py_sys.argv, list),
            "stderr_exists": py_sys.stderr is not None,
            "stdout_exists": py_sys.stdout is not None,
            "path_is_list": isinstance(py_sys.path, list),
        }
    if name == "sys_setters":
        old_argv = list(py_sys.argv)
        old_path = list(py_sys.path)
        try:
            py_sys.set_argv(["a", "b"])
            py_sys.set_path(["x"])
            return {"argv": list(py_sys.argv), "path": list(py_sys.path)}
        finally:
            py_sys.set_argv(old_argv)
            py_sys.set_path(old_path)
    if name == "typing_exports":
        values = [
            py_typing.Any,
            py_typing.List,
            py_typing.Set,
            py_typing.Dict,
            py_typing.Tuple,
            py_typing.Iterable,
            py_typing.Optional,
            py_typing.Union,
            py_typing.Callable,
        ]
        return {"all_present": all(v is not None for v in values)}
    if name == "typing_typevar_callable":
        t = py_typing.TypeVar("T")
        return {"typevar_exists": t is not None, "callable_exists": py_typing.Callable is not None}
    raise AssertionError(f"unknown pylib case: {name}")


def _get_path(doc: Any, path_expr: str) -> Any:
    cur = doc
    for part in path_expr.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def _assert_case(path: Path, result: dict[str, Any], assertion: dict[str, Any]) -> None:
    path_expr = assertion.get("path")
    if not isinstance(path_expr, str):
        raise AssertionError(f"{path}: assertion path must be a string")
    actual = _get_path(result, path_expr)
    if "equals" in assertion:
        assert actual == assertion["equals"], f"{path}: {path_expr} = {actual!r}"
    if "exists" in assertion:
        expected = bool(assertion["exists"])
        assert (actual is not _MISSING) is expected, f"{path}: exists mismatch at {path_expr}"


def _run_pylib_case(path: Path) -> None:
    case = _load_case(path)
    name = case.get("case")
    if not isinstance(name, str):
        raise AssertionError(f"{path}: case must be a string")
    result = _run_named_case(name)
    assertions = case.get("assertions", [])
    if not isinstance(assertions, list):
        raise AssertionError(f"{path}: assertions must be a list")
    for assertion in assertions:
        if not isinstance(assertion, dict):
            raise AssertionError(f"{path}: assertion must be an object")
        _assert_case(path, result, assertion)


if pytest is not None:

    @pytest.mark.parametrize("path", _case_paths(), ids=_case_id)
    def test_pylib_case(path: Path) -> None:
        _run_pylib_case(path)

else:

    class PyLibCaseTests(unittest.TestCase):
        def test_pylib_cases(self) -> None:
            for path in _case_paths():
                with self.subTest(case=_case_id(path)):
                    _run_pylib_case(path)


if __name__ == "__main__":
    unittest.main()
