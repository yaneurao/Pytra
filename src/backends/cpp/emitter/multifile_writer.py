from __future__ import annotations

from pytra.std import os as _os
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.typing import Any
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

_RUNTIME_EAST_ROOT_STR = str(Path(__file__).resolve().parents[3] / "runtime" / "generated")
_RUNTIME_CPP_ROOT_STR = str(Path(__file__).resolve().parents[3] / "runtime" / "cpp")


def _is_runtime_module_path(path_str: str) -> bool:
    """Check if a module path is under the runtime/generated directory."""
    try:
        resolved = str(Path(path_str).resolve())
        return resolved.startswith(_RUNTIME_EAST_ROOT_STR)
    except Exception:
        return False


def _runtime_module_bucket_and_stem(path_str: str) -> tuple[str, str]:
    """Extract bucket (built_in/std/utils) and stem from runtime .east path."""
    resolved = str(Path(path_str).resolve())
    rel = resolved[len(_RUNTIME_EAST_ROOT_STR):].lstrip("/").lstrip("\\")
    parts = rel.replace("\\", "/").split("/")
    if len(parts) == 2:
        bucket = parts[0]
        stem = parts[1]
        if stem.endswith(".east"):
            stem = stem[:-5]
        return bucket, stem
    return "", ""


def _runtime_module_has_native_cpp(bucket: str, stem: str) -> bool:
    """Check if a runtime module has a native .cpp implementation."""
    native_cpp = _os.path.join(_RUNTIME_CPP_ROOT_STR, bucket, stem + ".cpp")
    return _os.path.isfile(native_cpp)


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
        is_rt = _is_runtime_module_path(mod_key)
        if is_rt:
            rt_bucket, rt_stem = _runtime_module_bucket_and_stem(mod_key)
            label = rt_bucket + "/" + rt_stem if rt_bucket != "" else module_rel_label(root, mod_path)
        else:
            label = module_rel_label(root, mod_path)
        module_label_map[mod_key] = label
        mod_name = module_id_from_east_for_graph(root, mod_path, east0)
        if mod_name != "":
            if is_rt and rt_bucket != "":
                ns = "pytra::std::" + rt_stem if rt_bucket == "std" else ("pytra::utils::" + rt_stem if rt_bucket == "utils" else "pytra::" + rt_bucket + "::" + rt_stem)
                module_ns_map[mod_name] = ns
            else:
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
        is_runtime = _is_runtime_module_path(mod_key)
        if is_runtime:
            bucket, stem = _runtime_module_bucket_and_stem(mod_key)
            label = bucket + "/" + stem if bucket != "" else label
            is_extern = _runtime_module_has_native_cpp(bucket, stem)
        else:
            is_extern = False
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

        if is_runtime and bucket != "" and stem != "":
            emitter_ns = "pytra::std::" + stem if bucket == "std" else ("pytra::utils::" + stem if bucket == "utils" else "pytra::" + bucket + "::" + stem)
        else:
            emitter_ns = "pytra_mod_" + label
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
            emitter_ns,
            emit_main if is_entry else False,
        )
        type_emitter.enable_helper_artifact_lane = True
        type_emitter.user_module_east_map = module_doc_by_name
        cpp_txt = type_emitter.transpile()
        helper_artifacts = type_emitter.finalize_helper_artifacts()

        # multi-file モードでは共通 prelude を使い、ランタイム include 重複を避ける。
        # runtime モジュールは "runtime/cpp/..." パスで emit されることがあるので正規化する。
        cpp_txt = replace_first(
            cpp_txt,
            '#include "runtime/cpp/core/py_runtime.h"',
            '#include "core/py_runtime.h"',
        )
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
            top_namespace=emitter_ns,
            cpp_text=cpp_txt,
        )
        if is_runtime:
            # out/cpp/ 自己完結ビルドでは runtime/cpp/ prefix を除去する。
            hdr_text = hdr_text.replace('#include "runtime/cpp/', '#include "')
            cpp_txt = cpp_txt.replace('#include "runtime/cpp/', '#include "')
            rendered_modules.append(
                {
                    "module": mod_key,
                    "kind": "runtime",
                    "label": label,
                    "header_text": hdr_text,
                    "source_text": cpp_txt if not is_extern else "// @extern: " + label,
                    "is_entry": False,
                }
            )
        else:
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
