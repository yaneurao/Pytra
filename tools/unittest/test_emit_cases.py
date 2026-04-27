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

from toolchain.emit.cpp.emitter import CppEmitContext
from toolchain.emit.cpp.emitter import _emit_expr as emit_cpp_expr
from toolchain.emit.cpp.emitter import _emit_stmt as emit_cpp_stmt


CASE_ROOT = ROOT / "test" / "cases" / "emit"


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


def _assert_rendered(path: Path, case: dict[str, Any], rendered: str) -> None:
    if "expected" in case:
        assert rendered == case["expected"], path
    for item in case.get("expected_contains", []):
        assert item in rendered, f"{path}: expected {item!r} in {rendered!r}"
    for item in case.get("expected_not_contains", []):
        assert item not in rendered, f"{path}: expected {item!r} not in {rendered!r}"


def _emit_cpp_case(case: dict[str, Any]) -> str:
    level = case.get("level")
    node = case.get("input")
    if level == "expr":
        return emit_cpp_expr(CppEmitContext(), node)
    if level == "stmt":
        ctx = CppEmitContext()
        emit_cpp_stmt(ctx, node)
        return "\n".join(ctx.lines)
    raise AssertionError(f"unsupported cpp emit case level: {level!r}")


def _run_emit_case(path: Path) -> None:
    case = _load_case(path)
    target = case.get("target")
    if target == "cpp":
        rendered = _emit_cpp_case(case)
    else:
        raise AssertionError(f"{path}: unsupported target {target!r}")
    _assert_rendered(path, case, rendered)


if pytest is not None:

    @pytest.mark.parametrize("path", _case_paths(), ids=_case_id)
    def test_emit_case(path: Path) -> None:
        _run_emit_case(path)

else:

    class EmitCaseTests(unittest.TestCase):
        def test_emit_cases(self) -> None:
            for path in _case_paths():
                with self.subTest(case=_case_id(path)):
                    _run_emit_case(path)


if __name__ == "__main__":
    unittest.main()
