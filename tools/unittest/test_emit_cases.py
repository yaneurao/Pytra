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
from toolchain.emit.cpp.emitter import emit_cpp_module
from toolchain.emit.cs.emitter import emit_cs_module
from toolchain.emit.dart.emitter import emit_dart_module
from toolchain.compile.lower import lower_east2_to_east3
from toolchain.emit.go.emitter import emit_go_module
from toolchain.emit.java.emitter import emit_java_module
from toolchain.emit.julia.emitter import emit_julia_module
from toolchain.emit.kotlin.emitter import emit_kotlin_module
from toolchain.emit.lua.emitter import emit_lua_module
from toolchain.emit.nim.emitter import emit_nim_module
from toolchain.emit.php.emitter import emit_php_module
from toolchain.emit.powershell.emitter import emit_ps1_module
from toolchain.emit.ruby.emitter import emit_ruby_module
from toolchain.emit.rs.emitter import emit_rs_module
from toolchain.emit.scala.emitter import emit_scala_module
from toolchain.emit.swift.emitter import emit_swift_module
from toolchain.emit.ts.emitter import emit_ts_module
from toolchain.parse.py.parser import parse_python_source
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import resolve_east1_to_east2


CASE_ROOT = ROOT / "test" / "cases" / "emit"
_REGISTRY: Any | None = None


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


def _fixture_path(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixture" / "source" / "py").rglob(stem + ".py"))
    if len(matches) == 0:
        raise FileNotFoundError("missing fixture: " + stem)
    return matches[0]


def _build_east3_from_source(source: str, source_path: str, target: str) -> dict[str, Any]:
    target_language = "ts" if target == "js" else target
    east = parse_python_source(source, source_path).to_jv()
    resolve_east1_to_east2(east, registry=_registry())
    return lower_east2_to_east3(east, target_language=target_language)


def _module_input(case: dict[str, Any]) -> tuple[str, str]:
    source = case.get("input")
    if isinstance(source, str):
        return source, "<case>"
    fixture = case.get("fixture")
    if isinstance(fixture, str):
        path = _fixture_path(fixture)
        return path.read_text(encoding="utf-8"), str(path)
    raise AssertionError("module emit case requires input or fixture")


def _emit_module_case(target: str, case: dict[str, Any]) -> str:
    source, source_path = _module_input(case)
    east3 = _build_east3_from_source(source, source_path, target)
    if target == "cpp":
        return emit_cpp_module(east3)
    if target == "cs":
        return emit_cs_module(east3)
    if target == "dart":
        return emit_dart_module(east3)
    if target == "go":
        return emit_go_module(east3)
    if target == "java":
        return emit_java_module(east3)
    if target == "julia":
        return emit_julia_module(east3)
    if target == "kotlin":
        return emit_kotlin_module(east3)
    if target == "lua":
        return emit_lua_module(east3)
    if target == "nim":
        return emit_nim_module(east3)
    if target == "php":
        return emit_php_module(east3)
    if target == "powershell":
        return emit_ps1_module(east3)
    if target == "rb":
        return emit_ruby_module(east3)
    if target == "rs":
        return emit_rs_module(east3)
    if target == "scala":
        return emit_scala_module(east3)
    if target == "swift":
        return emit_swift_module(east3)
    if target == "ts":
        return emit_ts_module(east3)
    if target == "js":
        return emit_ts_module(east3, strip_types=True)
    raise AssertionError(f"unsupported module emit target: {target!r}")


def _run_emit_case(path: Path) -> None:
    case = _load_case(path)
    target = case.get("target")
    level = case.get("level")
    if target == "cpp" and level != "module":
        rendered = _emit_cpp_case(case)
    elif isinstance(target, str) and level == "module":
        rendered = _emit_module_case(target, case)
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
