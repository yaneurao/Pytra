from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path
from typing import Any
from toolchain.compiler.transpile_cli import (
    dict_any_get_dict,
    dict_any_get_str,
    inject_after_includes_block,
    join_str_list,
    module_id_from_east_for_graph,
    module_rel_label,
    path_parent_text,
    sort_str_list_copy,
    replace_first,
    write_text_file,
)

from backends.cpp.program_writer import write_cpp_rendered_program
from backends.cpp.emitter.cpp_emitter import CppEmitter
from backends.cpp.emitter.runtime_paths import module_name_to_cpp_include
from toolchain.json_adapters import dumps_object as _json_dumps_object
from backends.cpp.emitter.header_builder import build_cpp_header_from_east
from backends.cpp.optimizer import optimize_cpp_ir
from backends.cpp.optimizer import render_cpp_opt_trace


def write_multi_file_cpp(
    entry_path: Path,
    module_east_map: dict[str, dict[str, Any]],
    output_dir: Path,
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
    top_namespace: str,
    emit_main: bool,
    cpp_opt_level: str | int | object = 1,
    cpp_opt_pass: str = "",
    dump_cpp_ir_before_opt: str = "",
    dump_cpp_ir_after_opt: str = "",
    dump_cpp_opt_trace: str = "",
    max_generated_lines: int = 0,
    cpp_list_model: str = "",
) -> dict[str, Any]:
    """Legacy facade that renders module texts then delegates layout/manifest writing."""
    _ = top_namespace

    root = Path(path_parent_text(entry_path))
    entry_key = str(entry_path)
    files: list[str] = []
    for mod_key in module_east_map:
        files.append(mod_key)
    files = sort_str_list_copy(files)
    module_ns_map: dict[str, str] = {}
    module_label_map: dict[str, str] = {}
    module_key_by_name: dict[str, str] = {}
    module_doc_by_name: dict[str, dict[str, Any]] = {}
    for mod_key in files:
        mod_path = Path(mod_key)
        east0 = dict_any_get_dict(module_east_map, mod_key)
        label = module_rel_label(root, mod_path)
        module_label_map[mod_key] = label
        mod_name = module_id_from_east_for_graph(root, mod_path, east0)
        if mod_name != "":
            module_ns_map[mod_name] = "pytra_mod_" + label
            if mod_name not in module_key_by_name:
                module_key_by_name[mod_name] = mod_key
            module_doc_by_name[mod_name] = east0

    rendered_modules: list[dict[str, Any]] = []
    seen_helper_module_ids: set[str] = set()

    def _write_debug_text(path_txt: str, text: str) -> None:
        if path_txt == "":
            return
        out_path = Path(path_txt)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_file(out_path, text)

    for mod_key in files:
        east = dict_any_get_dict(module_east_map, mod_key)
        if len(east) == 0:
            continue
        mod_path = Path(mod_key)
        label = module_label_map[mod_key] if mod_key in module_label_map else ""
        is_entry = mod_key == entry_key
        optimized_east: dict[str, Any] = east
        if isinstance(east, dict):
            if is_entry and dump_cpp_ir_before_opt != "":
                _write_debug_text(
                    dump_cpp_ir_before_opt,
                    _json_dumps_object(east, ensure_ascii=False, indent=2) + "\n",
                )
            optimized_east, cpp_opt_report = optimize_cpp_ir(
                east,
                opt_level=cpp_opt_level,
                opt_pass_spec=cpp_opt_pass,
                debug_flags={
                    "negative_index_mode": negative_index_mode,
                    "bounds_check_mode": bounds_check_mode,
                    "floor_div_mode": floor_div_mode,
                    "mod_mode": mod_mode,
                    "int_width": int_width,
                    "str_index_mode": str_index_mode,
                    "str_slice_mode": str_slice_mode,
                    "opt_level": opt_level,
                },
            )
            if is_entry and dump_cpp_ir_after_opt != "":
                _write_debug_text(
                    dump_cpp_ir_after_opt,
                    _json_dumps_object(optimized_east, ensure_ascii=False, indent=2) + "\n",
                )
            if is_entry and dump_cpp_opt_trace != "":
                _write_debug_text(dump_cpp_opt_trace, render_cpp_opt_trace(cpp_opt_report))
        module_name = module_id_from_east_for_graph(root, mod_path, optimized_east)
        if module_name != "":
            module_doc_by_name[module_name] = optimized_east

        type_emitter = CppEmitter(
            optimized_east,
            module_ns_map,
            negative_index_mode,
            bounds_check_mode,
            floor_div_mode,
            mod_mode,
            int_width,
            str_index_mode,
            str_slice_mode,
            opt_level,
            "pytra_mod_" + label,
            emit_main if is_entry else False,
        )
        type_emitter.enable_helper_artifact_lane = True
        if cpp_list_model in {"value", "pyobj"}:
            type_emitter.cpp_list_model = cpp_list_model
        type_emitter.user_module_east_map = module_doc_by_name
        cpp_txt = type_emitter.transpile()
        helper_artifacts = type_emitter.finalize_helper_artifacts()

        # multi-file モードでは共通 prelude を使い、ランタイム include 重複を避ける。
        cpp_txt = replace_first(
            cpp_txt,
            '#include "core/py_runtime.h"',
            '#include "pytra_multi_prelude.h"',
        )
        # ユーザーモジュール import 呼び出しを解決するため、参照先関数の前方宣言を補う。
        meta = dict_any_get_dict(east, "meta")
        import_modules = dict_any_get_dict(meta, "import_modules")
        import_symbols = dict_any_get_dict(meta, "import_symbols")
        dep_modules: set[str] = set()
        for module_id_obj in import_modules.values():
            if isinstance(module_id_obj, str) and module_id_obj:
                dep_modules.add(module_id_obj)
        for sym_obj in import_symbols.values():
            if not isinstance(sym_obj, dict):
                continue
            module_id = dict_any_get_str(sym_obj, "module")
            export_name = dict_any_get_str(sym_obj, "name")
            if module_id and export_name:
                # e.g. module="pytra.std", name="os_path" → "pytra.std.os_path"
                dep_modules.add(module_id + "." + export_name)
            elif module_id:
                dep_modules.add(module_id)
        # Also use import_bindings for more precise resolution.
        bindings = meta.get("import_bindings")
        if isinstance(bindings, list):
            for binding in bindings:
                if not isinstance(binding, dict):
                    continue
                mod_id = dict_any_get_str(binding, "module_id")
                export_name = dict_any_get_str(binding, "export_name")
                if mod_id and export_name:
                    dep_modules.add(mod_id + "." + export_name)
                elif mod_id:
                    dep_modules.add(mod_id)

        dep_include_lines: list[str] = []
        seen_dep_includes: set[str] = set()
        for mod_name in dep_modules:
            target_key = module_key_by_name.get(mod_name, "")
            if target_key != "" and target_key != mod_key:
                # User module → include by label
                dep_label = module_label_map.get(target_key, "")
                if dep_label != "":
                    include_line = f'#include "{dep_label}.h"'
                    if include_line not in seen_dep_includes:
                        seen_dep_includes.add(include_line)
                        dep_include_lines.append(include_line)
            else:
                # Runtime module → resolve via runtime_symbol_index
                runtime_inc = module_name_to_cpp_include(mod_name)
                if runtime_inc != "":
                    include_line = f'#include "{runtime_inc}"'
                    if include_line not in seen_dep_includes:
                        seen_dep_includes.add(include_line)
                        dep_include_lines.append(include_line)

        if len(dep_include_lines) > 0:
            cpp_txt = inject_after_includes_block(cpp_txt, join_str_list("\n", dep_include_lines))
        hdr_text = build_cpp_header_from_east(
            optimized_east,
            mod_path,
            output_dir / "include" / f"{label}.h",
            top_namespace="pytra_mod_" + label,
            cpp_text=cpp_txt,
            cpp_list_model=cpp_list_model,
        )
        rendered_modules.append(
            {
                "module": mod_key,
                "label": label,
                "header_text": hdr_text,
                "source_text": cpp_txt,
                "is_entry": is_entry,
            }
        )
        for helper in helper_artifacts:
            if not isinstance(helper, dict):
                continue
            helper_module_id = dict_any_get_str(helper, "module_id")
            if helper_module_id == "" or helper_module_id in seen_helper_module_ids:
                continue
            helper_meta = dict_any_get_dict(helper, "metadata")
            helper_label = dict_any_get_str(helper, "label")
            helper_header = dict_any_get_str(helper_meta, "header_text")
            helper_source = dict_any_get_str(helper_meta, "source_text")
            if helper_label == "" or helper_header == "" or helper_source == "":
                continue
            seen_helper_module_ids.add(helper_module_id)
            rendered_modules.append(
                {
                    "module": helper_module_id,
                    "kind": dict_any_get_str(helper, "kind", "helper"),
                    "helper_id": dict_any_get_str(helper_meta, "helper_id"),
                    "owner_module_id": dict_any_get_str(helper_meta, "owner_module_id"),
                    "label": helper_label,
                    "header_text": helper_header,
                    "source_text": helper_source,
                    "is_entry": False,
                }
            )
    return write_cpp_rendered_program(
        output_dir,
        rendered_modules,
        entry=entry_key,
        entry_modules=[entry_key],
        program_id=entry_key,
        max_generated_lines=max_generated_lines,
    )
