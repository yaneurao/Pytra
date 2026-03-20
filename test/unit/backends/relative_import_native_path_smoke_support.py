from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from toolchain.emit.go.emitter import transpile_to_go_native
from toolchain.emit.nim.emitter import transpile_to_nim_native
from toolchain.emit.swift.emitter import transpile_to_swift_native
from toolchain.compiler.relative_import_native_path_bundle_contract import (
    RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_SCENARIOS_V1,
)
from toolchain.frontends.transpile_cli import build_module_east_map, load_east3_document


def relative_import_native_path_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_NATIVE_PATH_BUNDLE_SCENARIOS_V1
    }


def write_relative_import_native_path_project(
    td_path: Path,
    *,
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
    helper_path.write_text("X = 3\ndef f() -> int:\n    return 7\n", encoding="utf-8")
    entry_path.write_text(f"{import_form}\n\n{body_text}", encoding="utf-8")
    return entry_path


def transpile_relative_import_native_path_project(
    root: Path,
    scenario_id: str,
    target: str,
) -> str:
    scenario = relative_import_native_path_scenarios()[scenario_id]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = write_relative_import_native_path_project(
            td_path,
            import_form=str(scenario["import_form"]),
            body_text=(
                "def _case_main() -> int:\n"
                f"    return {scenario['representative_expr']}\n"
            ),
        )
        out = td_path / f"main.{target}"
        proc = subprocess.run(
            [
                "python3",
                str(root / "src" / "py2x.py"),
                str(entry_path),
                "--target",
                target,
                "-o",
                str(out),
            ],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        return out.read_text(encoding="utf-8")


def transpile_relative_import_native_path_expect_failure(
    root: Path,
    target: str,
    import_form: str,
    representative_expr: str,
) -> str:
    emitters = {
        "go": transpile_to_go_native,
        "nim": transpile_to_nim_native,
        "swift": transpile_to_swift_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = write_relative_import_native_path_project(
            td_path,
            import_form=import_form,
            body_text=(
                "def _case_main() -> int:\n"
                f"    return {representative_expr}\n"
            ),
        )
        east = load_east3_document(
            entry_path,
            parser_backend="self_hosted",
            target_lang=target,
        )
        try:
            emit(east if isinstance(east, dict) else {})
        except Exception as exc:
            return str(exc)
    raise AssertionError(f"expected failure for {target} relative-import project")


def transpile_relative_import_native_path_via_module_graph(
    *,
    target: str,
    import_form: str,
    body_text: str,
) -> str:
    emitters = {
        "go": transpile_to_go_native,
        "nim": transpile_to_nim_native,
        "swift": transpile_to_swift_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = write_relative_import_native_path_project(
            td_path,
            import_form=import_form,
            body_text=body_text,
        )

        def _load(
            input_path: Path,
            parser_backend: str = "self_hosted",
            east_stage: str = "3",
            object_dispatch_mode: str = "native",
        ) -> dict[str, object]:
            if east_stage != "3":
                raise RuntimeError("unsupported east_stage: " + east_stage)
            doc3 = load_east3_document(
                input_path,
                parser_backend=parser_backend,
                object_dispatch_mode=object_dispatch_mode,
                target_lang=target,
            )
            return doc3 if isinstance(doc3, dict) else {}

        module_map = build_module_east_map(
            entry_path,
            _load,
            parser_backend="self_hosted",
            east_stage="3",
            object_dispatch_mode="native",
        )
        east = module_map.get(str(entry_path), {})
        return emit(east if isinstance(east, dict) else {})


def relative_import_native_path_expected_rewrite(
    scenario_id: str,
) -> tuple[str, str]:
    if scenario_id == "parent_module_alias":
        return ("helper.f()", "h.f()")
    if scenario_id == "parent_symbol_alias":
        return ("helper.f()", "g()")
    raise KeyError(f"unknown native-path relative-import scenario: {scenario_id}")
