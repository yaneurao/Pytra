from __future__ import annotations

import tempfile
from pathlib import Path

from backends.java.emitter.java_native_emitter import transpile_to_java_native
from backends.kotlin.emitter import transpile_to_kotlin_native
from backends.scala.emitter import transpile_to_scala_native
from toolchain.compiler.relative_import_jvm_package_bundle_contract import (
    RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1,
)
from toolchain.compiler.transpile_cli import load_east3_document


def relative_import_jvm_package_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_JVM_PACKAGE_BUNDLE_SCENARIOS_V1
    }


def write_relative_import_jvm_package_project(
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
    helper_path.write_text("def f() -> int:\n    return 7\n", encoding="utf-8")
    entry_path.write_text(f"{import_form}\n\n{body_text}", encoding="utf-8")
    return entry_path


def _load_relative_import_jvm_package_east(entry_path: Path, target: str) -> dict[str, object]:
    east = load_east3_document(
        entry_path,
        parser_backend="self_hosted",
        target_lang=target,
    )
    return east if isinstance(east, dict) else {}


def transpile_relative_import_jvm_package_project(
    scenario_id: str,
    target: str,
) -> str:
    scenario = relative_import_jvm_package_scenarios()[scenario_id]
    emitters = {
        "java": lambda east: transpile_to_java_native(east, class_name="Main"),
        "kotlin": transpile_to_kotlin_native,
        "scala": transpile_to_scala_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        entry_path = write_relative_import_jvm_package_project(
            Path(td),
            import_form=str(scenario["import_form"]),
            body_text=(
                "def call() -> int:\n"
                f"    return {scenario['representative_expr']}\n"
            ),
        )
        east = _load_relative_import_jvm_package_east(entry_path, target)
        return emit(east)


def transpile_relative_import_jvm_package_expect_failure(
    target: str,
    import_form: str,
    representative_expr: str,
) -> str:
    emitters = {
        "java": lambda east: transpile_to_java_native(east, class_name="Main"),
        "kotlin": transpile_to_kotlin_native,
        "scala": transpile_to_scala_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        entry_path = write_relative_import_jvm_package_project(
            Path(td),
            import_form=import_form,
            body_text=(
                "def call() -> int:\n"
                f"    return {representative_expr}\n"
            ),
        )
        east = _load_relative_import_jvm_package_east(entry_path, target)
        try:
            emit(east)
        except Exception as exc:
            return str(exc)
    raise AssertionError(f"expected failure for {target} relative-import project")


def relative_import_jvm_package_expected_needles(
    target: str,
    scenario_id: str,
) -> tuple[str, str]:
    if scenario_id == "parent_module_alias":
        if target == "java":
            return ("return helper.f();", "return h.f();")
        return ("return __pytra_int(helper.f())", "return __pytra_int(h.f())")
    if scenario_id == "parent_symbol_alias":
        if target == "java":
            return ("return helper.f();", "return g();")
        return ("return __pytra_int(helper.f())", "return __pytra_int(g())")
    raise KeyError(f"unknown JVM-package relative-import scenario: {scenario_id}")
