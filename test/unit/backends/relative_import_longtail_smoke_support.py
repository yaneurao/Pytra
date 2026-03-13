from __future__ import annotations

import tempfile
from pathlib import Path

from backends.lua.emitter import transpile_to_lua_native
from backends.php.emitter import transpile_to_php_native
from backends.ruby.emitter import transpile_to_ruby_native
from toolchain.compiler.relative_import_longtail_support_contract import (
    RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1,
)
from toolchain.compiler.transpile_cli import build_module_east_map, load_east3_document


def relative_import_longtail_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_LONGTAIL_SUPPORT_SCENARIOS_V1
    }


def write_relative_import_longtail_project(
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


def _load_relative_import_longtail_east(entry_path: Path, target: str) -> dict[str, object]:
    east = load_east3_document(
        entry_path,
        parser_backend="self_hosted",
        target_lang=target,
    )
    return east if isinstance(east, dict) else {}


def transpile_relative_import_longtail_project(target: str, scenario_id: str) -> str:
    scenario = relative_import_longtail_scenarios()[scenario_id]
    emitters = {
        "lua": transpile_to_lua_native,
        "php": transpile_to_php_native,
        "ruby": transpile_to_ruby_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        entry_path = write_relative_import_longtail_project(
            Path(td),
            import_form=str(scenario["import_form"]),
            body_text=(
                "def call() -> int:\n"
                f"    return {scenario['representative_expr']}\n"
            ),
        )
        east = _load_relative_import_longtail_east(entry_path, target)
        return emit(east)


def transpile_relative_import_longtail_via_module_graph(
    *,
    target: str,
    import_form: str,
    body_text: str,
) -> str:
    emitters = {
        "lua": transpile_to_lua_native,
        "php": transpile_to_php_native,
        "ruby": transpile_to_ruby_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        entry_path = write_relative_import_longtail_project(
            Path(td),
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


def transpile_relative_import_longtail_expect_failure(
    target: str,
    import_form: str,
    representative_expr: str,
) -> str:
    emitters = {
        "lua": transpile_to_lua_native,
        "php": transpile_to_php_native,
        "ruby": transpile_to_ruby_native,
    }
    emit = emitters[target]
    with tempfile.TemporaryDirectory() as td:
        entry_path = write_relative_import_longtail_project(
            Path(td),
            import_form=import_form,
            body_text=(
                "def call() -> int:\n"
                f"    return {representative_expr}\n"
            ),
        )
        east = _load_relative_import_longtail_east(entry_path, target)
        try:
            emit(east)
        except Exception as exc:
            return str(exc)
    raise AssertionError(f"expected failure for {target} relative-import project")


def relative_import_longtail_expected_rewrite(
    scenario_id: str,
) -> tuple[str, str]:
    if scenario_id == "parent_module_alias":
        return ("helper.f()", "h.f()")
    if scenario_id == "parent_symbol_alias":
        return ("helper.f()", "g()")
    raise KeyError(f"unknown long-tail relative-import scenario: {scenario_id}")
