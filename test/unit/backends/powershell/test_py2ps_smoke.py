"""py2powershell (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "test" / "unit" / "backends") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit" / "backends"))

from toolchain.emit.powershell.emitter import load_powershell_profile, transpile_to_powershell
from toolchain.misc.transpile_cli import load_east3_document

def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
):
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="js",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2PowerShellSmokeTest(unittest.TestCase):
    def test_load_powershell_profile_contains_core_sections(self) -> None:
        profile = load_powershell_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_transpiles(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertTrue(ps.strip())
        self.assertIn("#Requires -Version 5.1", ps)

    def test_output_contains_powershell_header(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("Set-StrictMode -Version Latest", ps)
        self.assertIn("$ErrorActionPreference", ps)
        self.assertIn("py_runtime.ps1", ps)

    def test_secondary_bundle_representative_fixtures_transpile_for_powershell(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "for_range",
            "try_raise",
            "enumerate_basic",
            "is_instance",
        ):
            with self.subTest(stem=stem):
                fixture = find_fixture_case(stem)
                east = load_east(fixture, parser_backend="self_hosted")
                ps = transpile_to_powershell(east)
                self.assertTrue(ps.strip())

    def test_function_emits_powershell_function_keyword(self) -> None:
        fixture = find_fixture_case("lambda_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("function ", ps)

    def test_for_loop_emits_powershell_for_or_foreach(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        has_for = "for (" in ps or "foreach (" in ps
        self.assertTrue(has_for, "Expected 'for (' or 'foreach (' in PowerShell output")

    def test_if_emits_powershell_if_block(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("if (", ps)

    def test_cli_transpile_powershell_via_py2x(self) -> None:
        fixture = find_fixture_case("class_body_pass")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "test.ps1"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            cmd = [
                sys.executable, str(ROOT / "src" / "pytra-cli.py"),
                "--target", "powershell",
                str(fixture),
                "-o", str(out),
            ]
            proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
            text = out.read_text(encoding="utf-8")
            self.assertIn("#Requires -Version 5.1", text)


RUNTIME_PS1 = ROOT / "src" / "runtime" / "powershell" / "built_in" / "py_runtime.ps1"


def _find_pwsh() -> str | None:
    """Return pwsh path if available, else None."""
    for candidate in ("/tmp/pwsh/pwsh", "pwsh"):
        try:
            proc = subprocess.run(
                [candidate, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if proc.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _transpile_and_run(
    fixture_path: Path,
    *,
    pwsh: str,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    """Transpile a fixture to PowerShell and run it with pwsh."""
    env = dict(os.environ)
    py_path = str(ROOT / "src")
    old = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old

    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        stem = fixture_path.stem

        # Stage 1: transpile (pytra-cli outputs to out_dir/emit/)
        cmd = [
            sys.executable, str(ROOT / "src" / "pytra-cli.py"),
            "--target", "powershell",
            str(fixture_path),
            "--output-dir", str(out_dir),
        ]
        tp = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        if tp.returncode != 0:
            return tp  # transpile failure

        # Find the entry PS1 in emit/ directory
        emit_dir = out_dir / "emit"
        out_ps1 = emit_dir / (stem + ".ps1")
        if not out_ps1.exists():
            # Fallback: check out_dir directly (legacy)
            out_ps1 = out_dir / (stem + ".ps1")

        # Stage 2: run with pwsh
        return subprocess.run(
            [pwsh, "-File", str(out_ps1)],
            capture_output=True, text=True, timeout=timeout,
        )


_PWSH = _find_pwsh()


@unittest.skipIf(_PWSH is None, "pwsh not found")
class Py2PowerShellExecTest(unittest.TestCase):
    """pwsh 実行テスト: 主要 fixture が実行成功することを検証する。"""

    def _run_fixture(self, stem: str, *, timeout: int = 10) -> None:
        fixture = find_fixture_case(stem)
        result = _transpile_and_run(fixture, pwsh=_PWSH, timeout=timeout)
        self.assertEqual(
            result.returncode, 0,
            msg=f"pwsh execution failed for {stem}:\nstdout={result.stdout}\nstderr={result.stderr}",
        )

    # --- 基本演算 ---
    def test_exec_add(self) -> None:
        self._run_fixture("add")

    def test_exec_sub_mul(self) -> None:
        self._run_fixture("sub_mul")

    def test_exec_fib(self) -> None:
        self._run_fixture("fib")

    def test_exec_compare(self) -> None:
        self._run_fixture("compare")

    # --- 制御構文 ---
    def test_exec_if_else(self) -> None:
        self._run_fixture("if_else")

    def test_exec_for_range(self) -> None:
        self._run_fixture("for_range")

    def test_exec_loop(self) -> None:
        self._run_fixture("loop")

    def test_exec_try_raise(self) -> None:
        self._run_fixture("try_raise")

    # --- 文字列 ---
    def test_exec_fstring(self) -> None:
        self._run_fixture("fstring")

    def test_exec_str_methods(self) -> None:
        self._run_fixture("str_methods")

    def test_exec_string_ops(self) -> None:
        self._run_fixture("string_ops")

    # --- コレクション ---
    def test_exec_comprehension(self) -> None:
        self._run_fixture("comprehension")

    def test_exec_dict_in(self) -> None:
        self._run_fixture("dict_in")

    def test_exec_negative_index(self) -> None:
        self._run_fixture("negative_index")

    def test_exec_slice_basic(self) -> None:
        self._run_fixture("slice_basic")

    # --- ラムダ ---
    def test_exec_lambda_basic(self) -> None:
        self._run_fixture("lambda_basic")

    def test_exec_lambda_as_arg(self) -> None:
        self._run_fixture("lambda_as_arg")

    # --- OOP ---
    def test_exec_class(self) -> None:
        self._run_fixture("class")

    def test_exec_class_instance(self) -> None:
        self._run_fixture("class_instance")

    def test_exec_inheritance(self) -> None:
        self._run_fixture("inheritance")

    def test_exec_super_init(self) -> None:
        self._run_fixture("super_init")

    # --- タプル/代入 ---
    def test_exec_tuple_assign(self) -> None:
        self._run_fixture("tuple_assign")

    def test_exec_assign(self) -> None:
        self._run_fixture("assign")

    # --- enumerate/reversed ---
    def test_exec_enumerate_basic(self) -> None:
        self._run_fixture("enumerate_basic")

    # --- math ---
    def test_exec_from_pytra_std_import_math(self) -> None:
        self._run_fixture("from_pytra_std_import_math")

    # --- range downcount ---
    def test_exec_range_downcount_len_minus1(self) -> None:
        self._run_fixture("range_downcount_len_minus1")

    # --- Python 出力一致検証 ---
    def _assert_output_matches_python(self, stem: str, *, timeout: int = 10) -> None:
        """transpile + pwsh 実行し、Python 実行結果と stdout が一致するか検証する。"""
        fixture = find_fixture_case(stem)
        env = dict(os.environ)
        py_path = str(ROOT / "src")
        old = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old

        py_proc = subprocess.run(
            [sys.executable, str(fixture)],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        self.assertEqual(py_proc.returncode, 0, msg=f"Python run failed for {stem}")
        py_out = py_proc.stdout.strip()

        ps_result = _transpile_and_run(fixture, pwsh=_PWSH, timeout=timeout)
        self.assertEqual(ps_result.returncode, 0, msg=f"pwsh failed for {stem}:\n{ps_result.stderr}")
        ps_out = ps_result.stdout.strip()

        self.assertEqual(py_out, ps_out, msg=f"Output mismatch for {stem}")

    def test_output_match_add(self) -> None:
        self._assert_output_matches_python("add")

    def test_output_match_fib(self) -> None:
        self._assert_output_matches_python("fib")

    def test_output_match_compare(self) -> None:
        self._assert_output_matches_python("compare")

    def test_output_match_if_else(self) -> None:
        self._assert_output_matches_python("if_else")

    def test_output_match_for_range(self) -> None:
        self._assert_output_matches_python("for_range")

    def test_output_match_loop(self) -> None:
        self._assert_output_matches_python("loop")

    def test_output_match_lambda_basic(self) -> None:
        self._assert_output_matches_python("lambda_basic")

    def test_output_match_tuple_assign(self) -> None:
        self._assert_output_matches_python("tuple_assign")

    def test_output_match_class(self) -> None:
        self._assert_output_matches_python("class")

    def test_output_match_inheritance(self) -> None:
        self._assert_output_matches_python("inheritance")

    def test_output_match_super_init(self) -> None:
        self._assert_output_matches_python("super_init")

    def test_output_match_fstring(self) -> None:
        self._assert_output_matches_python("fstring")

    def test_output_match_string_ops(self) -> None:
        self._assert_output_matches_python("string_ops")


if __name__ == "__main__":
    unittest.main()
