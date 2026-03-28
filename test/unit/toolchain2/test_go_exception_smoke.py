from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.emit.go.emitter import emit_go_module
from toolchain2.parse.py.parser import parse_python_source
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2


ROOT = Path(__file__).resolve().parents[3]


def _load_registry():
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


def _run_go(source: str, *, type_info_table: dict[str, object] | None = None) -> str:
    run = _run_go_process(source, type_info_table=type_info_table)
    if run.returncode != 0:
        raise AssertionError(f"{run.stdout}\n{run.stderr}")
    return run.stdout


def _run_go_process(
    source: str,
    *,
    type_info_table: dict[str, object] | None = None,
) -> subprocess.CompletedProcess[str]:
    east2 = parse_python_source(source, "<go-exception-smoke>").to_jv()
    resolve_east1_to_east2(east2, registry=_load_registry())
    east3 = lower_east2_to_east3(east2, target_language="go")
    meta = east3.setdefault("meta", {})
    assert isinstance(meta, dict)
    meta["emit_context"] = {"module_id": "app", "is_entry": True}
    if type_info_table is not None:
        meta["linked_program_v1"] = {"type_info_table_v1": type_info_table}
    go_code = emit_go_module(east3)

    with tempfile.TemporaryDirectory() as tmp:
        go_path = Path(tmp) / "app.go"
        runtime_path = ROOT / "src" / "runtime" / "go" / "built_in" / "py_runtime.go"
        bundled_runtime = Path(tmp) / "py_runtime.go"
        out_path = Path(tmp) / "app"
        go_path.write_text(go_code, encoding="utf-8")
        bundled_runtime.write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
        build = subprocess.run(
            ["go", "build", "-o", str(out_path), str(bundled_runtime), str(go_path)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            raise AssertionError(f"{build.stdout}\n{build.stderr}")
        run = subprocess.run([str(out_path)], cwd=tmp, capture_output=True, text=True)

    return run


SOURCE = """
def parse(flag: bool) -> int:
    if flag:
        raise ValueError("bad")
    return 7

if __name__ == "__main__":
    try:
        print(parse(False))
        print(parse(True))
    except ValueError as e:
        print(e)
    finally:
        print("done")
"""

MULTI_HANDLER_SOURCE = """
if __name__ == "__main__":
    try:
        raise IndexError("idx")
    except ValueError as e:
        print("value", e)
    except IndexError as e:
        print("index", e)
    finally:
        print("done")
"""

FINALLY_ONLY_SOURCE = """
if __name__ == "__main__":
    try:
        raise ValueError("boom")
    finally:
        print("cleanup")
"""

CUSTOM_EXCEPTION_SOURCE = """
class ParseError(ValueError):
    pass

if __name__ == "__main__":
    try:
        raise ParseError("bad parse")
    except ParseError as e:
        print(e)
"""

CUSTOM_EXCEPTION_BASE_CATCH_SOURCE = """
class ParseError(ValueError):
    pass

if __name__ == "__main__":
    try:
        raise ParseError("bad parse")
    except ValueError as e:
        print("value", e)
"""


class GoExceptionSmokeTests(unittest.TestCase):
    def test_go_emits_typed_value_error_catch_and_finally(self) -> None:
        stdout = _run_go(SOURCE)
        self.assertEqual(stdout, "7\nbad\ndone\n")

    def test_go_emits_multiple_exception_handlers(self) -> None:
        stdout = _run_go(MULTI_HANDLER_SOURCE)
        self.assertEqual(stdout, "index idx\ndone\n")

    def test_go_finally_runs_before_unhandled_rethrow(self) -> None:
        run = _run_go_process(FINALLY_ONLY_SOURCE)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, "cleanup\n")
        self.assertIn("boom", run.stderr)

    def test_go_emits_exact_custom_exception_catch(self) -> None:
        stdout = _run_go(
            CUSTOM_EXCEPTION_SOURCE,
            type_info_table={
                "app.ParseError": {"id": 1000, "entry": 1000, "exit": 1001},
            },
        )
        self.assertEqual(stdout, "bad parse\n")

    def test_go_builtin_base_handler_catches_custom_descendant(self) -> None:
        stdout = _run_go(
            CUSTOM_EXCEPTION_BASE_CATCH_SOURCE,
            type_info_table={
                "app.ParseError": {"id": 1000, "entry": 1000, "exit": 1001},
            },
        )
        self.assertEqual(stdout, "value bad parse\n")


if __name__ == "__main__":
    unittest.main()
