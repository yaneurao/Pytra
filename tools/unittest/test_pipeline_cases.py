from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any

try:
    import pytest
except ImportError:  # pragma: no cover - exercised in minimal local envs.
    pytest = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compile.lower import lower_east2_to_east3
from toolchain.parse.py.parser import parse_python_source
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import resolve_east1_to_east2


CASE_ROOT = ROOT / "test" / "cases"
PIPELINE_ROOTS = (CASE_ROOT / "east1", CASE_ROOT / "east2", CASE_ROOT / "east3")
_REGISTRY: Any | None = None
_MISSING = object()


def _case_paths() -> list[Path]:
    paths: list[Path] = []
    for root in PIPELINE_ROOTS:
        if root.exists():
            paths.extend(sorted(root.rglob("*.json")))
    return paths


def _case_id(path: Path) -> str:
    return path.relative_to(CASE_ROOT).with_suffix("").as_posix()


def _load_case(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)
    if not isinstance(case, dict):
        raise AssertionError(f"{path}: case root must be an object")
    return case


def _registry() -> Any:
    global _REGISTRY
    if _REGISTRY is None:
        include = ROOT / "test" / "include" / "east1" / "py"
        _REGISTRY = load_builtin_registry(
            include / "built_in" / "builtins.py.east1",
            include / "built_in" / "containers.py.east1",
            include / "std",
        )
    return _REGISTRY


def _build_pipeline(case: dict[str, Any]) -> dict[str, Any]:
    source = case.get("input")
    if not isinstance(source, str):
        raise AssertionError("pipeline case input must be a source string")
    pipeline = case.get("pipeline")
    east1 = parse_python_source(source, "<case>").to_jv()
    if pipeline == "source_to_east1":
        return east1
    resolve_east1_to_east2(east1, registry=_registry())
    if pipeline == "source_to_east2":
        return east1
    if pipeline == "source_to_east3":
        target_language = case.get("target_language", "core")
        if not isinstance(target_language, str):
            raise AssertionError("target_language must be a string")
        return lower_east2_to_east3(east1, target_language=target_language)
    raise AssertionError(f"unsupported pipeline: {pipeline!r}")


def _path_parts(path_expr: str) -> list[str | int]:
    parts: list[str | int] = []
    for segment in path_expr.split("."):
        rest = segment
        while rest:
            bracket = rest.find("[")
            if bracket < 0:
                parts.append(rest)
                rest = ""
                continue
            if bracket > 0:
                parts.append(rest[:bracket])
            end = rest.find("]", bracket)
            if end < 0:
                raise AssertionError(f"invalid path segment: {segment!r}")
            parts.append(int(rest[bracket + 1:end]))
            rest = rest[end + 1:]
    return parts


def _get_path(doc: Any, path_expr: str) -> Any:
    cur = doc
    for part in _path_parts(path_expr):
        if isinstance(part, int):
            if not isinstance(cur, list) or part >= len(cur):
                return _MISSING
            cur = cur[part]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return _MISSING
            cur = cur[part]
    return cur


def _assert_one(path: Path, doc: dict[str, Any], assertion: dict[str, Any]) -> None:
    path_expr = assertion.get("path")
    if not isinstance(path_expr, str):
        raise AssertionError(f"{path}: assertion path must be a string")
    actual = _get_path(doc, path_expr)
    if "exists" in assertion:
        expected = bool(assertion["exists"])
        assert (actual is not _MISSING) is expected, f"{path}: exists mismatch at {path_expr}"
    if "equals" in assertion:
        assert actual == assertion["equals"], f"{path}: {path_expr} = {actual!r}"
    if "not_equals" in assertion:
        assert actual != assertion["not_equals"], f"{path}: {path_expr} unexpectedly equals {actual!r}"
    if "contains" in assertion:
        expected_item = assertion["contains"]
        assert actual is not _MISSING, f"{path}: missing path {path_expr}"
        assert expected_item in actual, f"{path}: {expected_item!r} not in {actual!r}"


def _run_pipeline_case(path: Path) -> None:
    case = _load_case(path)
    doc = _build_pipeline(case)
    assertions = case.get("assertions", [])
    if not isinstance(assertions, list):
        raise AssertionError(f"{path}: assertions must be a list")
    for assertion in assertions:
        if not isinstance(assertion, dict):
            raise AssertionError(f"{path}: assertion must be an object")
        _assert_one(path, doc, assertion)


if pytest is not None:

    @pytest.mark.parametrize("path", _case_paths(), ids=_case_id)
    def test_pipeline_case(path: Path) -> None:
        _run_pipeline_case(path)

else:

    class PipelineCaseTests(unittest.TestCase):
        def test_pipeline_cases(self) -> None:
            for path in _case_paths():
                with self.subTest(case=_case_id(path)):
                    _run_pipeline_case(path)


if __name__ == "__main__":
    unittest.main()
