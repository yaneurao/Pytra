from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from toolchain.compiler.relative_import_secondwave_smoke_contract import (
    RELATIVE_IMPORT_SECOND_WAVE_SCENARIOS_V1,
)


def relative_import_secondwave_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_SECOND_WAVE_SCENARIOS_V1
    }


def write_relative_import_project(
    td_path: Path,
    import_form: str,
    body_text: str,
) -> Path:
    entry_path = td_path / "pkg" / "sub" / "main.py"
    helper_path = td_path / "pkg" / "helper.py"
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    helper_path.parent.mkdir(parents=True, exist_ok=True)
    for pkg_dir in {helper_path.parent, entry_path.parent}:
        current = pkg_dir
        while current != td_path and current.is_relative_to(td_path):
            init_py = current / "__init__.py"
            if not init_py.exists():
                init_py.write_text("", encoding="utf-8")
            current = current.parent
    helper_path.write_text("def f() -> int:\n    return 7\n", encoding="utf-8")
    entry_path.write_text(f"{import_form}\n{body_text}", encoding="utf-8")
    return entry_path


def transpile_relative_import_project(
    root: Path,
    scenario_id: str,
    target: str,
) -> str:
    scenario = relative_import_secondwave_scenarios()[scenario_id]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = write_relative_import_project(
            td_path,
            str(scenario["import_form"]),
            f"print({scenario['representative_expr']})\n",
        )
        out = td_path / f"main.{target}"
        proc = subprocess.run(
            ["python3", str(root / "src" / "py2x.py"), str(entry_path), "--target", target, "-o", str(out)],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        return out.read_text(encoding="utf-8")


def transpile_relative_import_project_expect_failure(
    root: Path,
    target: str,
    import_form: str,
    representative_expr: str,
) -> str:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = write_relative_import_project(
            td_path,
            import_form,
            f"print({representative_expr})\n",
        )
        out = td_path / f"main.{target}"
        proc = subprocess.run(
            ["python3", str(root / "src" / "py2x.py"), str(entry_path), "--target", target, "-o", str(out)],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            raise AssertionError(f"expected failure for {target} relative-import project")
        return proc.stderr


def relative_import_secondwave_expected_needles(
    scenario_id: str,
) -> tuple[str, str]:
    scenario = relative_import_secondwave_scenarios()[scenario_id]
    if scenario_id == "parent_module_alias":
        return (
            'import * as h from "./helper.js";',
            f"console.log({scenario['representative_expr']});",
        )
    if scenario_id == "parent_symbol_alias":
        return (
            'import { f as g } from "./helper.js";',
            f"console.log({scenario['representative_expr']});",
        )
    raise KeyError(f"unknown second-wave relative-import scenario: {scenario_id}")
