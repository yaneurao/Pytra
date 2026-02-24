from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path
from pytra.std.typing import Any
from pytra.compiler.east_parts.east1_build import East1BuildHelpers
from pytra.compiler.transpile_cli import (
    check_guard_limit,
    dict_any_get_dict,
    dict_any_get_list,
    dict_any_get_str,
    inject_after_includes_block,
    join_str_list,
    module_id_from_east_for_graph,
    module_rel_label,
    mkdirs_for_cli,
    path_parent_text,
    sanitize_module_label,
    sort_str_list_copy,
    count_text_lines,
    replace_first,
    write_text_file,
)

from hooks.cpp.emitter import CppEmitter


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
    max_generated_lines: int = 0,
) -> dict[str, Any]:
    """モジュールごとに `.h/.cpp` を `out/include`, `out/src` へ出力する。"""
    _ = top_namespace

    include_dir = output_dir / "include"
    src_dir = output_dir / "src"
    mkdirs_for_cli(str(include_dir))
    mkdirs_for_cli(str(src_dir))
    prelude_hdr = include_dir / "pytra_multi_prelude.h"
    prelude_txt = "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
    prelude_txt += "#ifndef PYTRA_MULTI_PRELUDE_H\n"
    prelude_txt += "#define PYTRA_MULTI_PRELUDE_H\n\n"
    prelude_txt += "#include \"runtime/cpp/pytra/built_in/py_runtime.h\"\n\n"
    prelude_txt += "#endif  // PYTRA_MULTI_PRELUDE_H\n"
    generated_lines_total = 0
    generated_lines_total += count_text_lines(prelude_txt)
    if max_generated_lines > 0:
        check_guard_limit("emit", "max_generated_lines", generated_lines_total, {"max_generated_lines": max_generated_lines})
    write_text_file(prelude_hdr, prelude_txt)

    root = Path(path_parent_text(entry_path))
    entry_key = str(entry_path)
    files: list[str] = []
    for mod_key in module_east_map:
        files.append(mod_key)
    files = sort_str_list_copy(files)
    module_ns_map: dict[str, str] = {}
    module_label_map: dict[str, str] = {}
    module_key_by_name: dict[str, str] = {}
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

    type_schema = East1BuildHelpers.build_module_type_schema(module_east_map)
    manifest_modules: list[dict[str, Any]] = []

    for mod_key in files:
        east = dict_any_get_dict(module_east_map, mod_key)
        if len(east) == 0:
            continue
        mod_path = Path(mod_key)
        label = module_label_map[mod_key] if mod_key in module_label_map else ""
        hdr_path = include_dir / (label + ".h")
        cpp_path = src_dir / (label + ".cpp")
        guard = "PYTRA_MULTI_" + sanitize_module_label(label).upper() + "_H"
        hdr_text = "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        hdr_text += "#ifndef " + guard + "\n"
        hdr_text += "#define " + guard + "\n\n"
        hdr_text += "namespace pytra_multi {\n"
        hdr_text += "void module_" + label + "();\n"
        hdr_text += "}  // namespace pytra_multi\n\n"
        hdr_text += "#endif  // " + guard + "\n"
        generated_lines_total += count_text_lines(hdr_text)
        if max_generated_lines > 0:
            check_guard_limit(
                "emit",
                "max_generated_lines",
                generated_lines_total,
                {"max_generated_lines": max_generated_lines},
                str(mod_path),
            )
        write_text_file(hdr_path, hdr_text)

        is_entry = mod_key == entry_key
        type_emitter = CppEmitter(
            east,
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
        cpp_txt = type_emitter.transpile()

        # multi-file モードでは共通 prelude を使い、ランタイム include 重複を避ける。
        cpp_txt = replace_first(
            cpp_txt,
            '#include "runtime/cpp/pytra/built_in/py_runtime.h"',
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
            module_id = dict_any_get_str(sym_obj if isinstance(sym_obj, dict) else {}, "module")
            if module_id:
                dep_modules.add(module_id)

        fwd_lines: list[str] = []
        for mod_name in dep_modules:
            target_ns = module_ns_map.get(mod_name, "")
            if target_ns == "":
                continue
            target_key = module_key_by_name.get(mod_name, "")
            if target_key == "":
                continue
            target_schema = dict_any_get_dict(type_schema, target_key)
            funcs = dict_any_get_dict(target_schema, "functions")
            # `main` は他モジュールから呼ばれない前提。
            fn_decls: list[str] = []
            for fn_name_any, fn_sig_obj in funcs.items():
                if not isinstance(fn_name_any, str):
                    continue
                if fn_name_any == "main":
                    continue
                fn_name = fn_name_any
                sig = fn_sig_obj if isinstance(fn_sig_obj, dict) else {}
                ret_t = dict_any_get_str(sig, "return_type", "None")
                ret_cpp = "void" if ret_t == "None" else type_emitter._cpp_type_text(ret_t)
                arg_types = dict_any_get_dict(sig, "arg_types")
                arg_order = dict_any_get_list(sig, "arg_order")
                parts: list[str] = []
                for an in arg_order:
                    if not isinstance(an, str):
                        continue
                    at = dict_any_get_str(arg_types, an, "object")
                    at_cpp = type_emitter._cpp_type_text(at)
                    parts.append(at_cpp + " " + an)
                sep = ", "
                fn_decls.append("    " + ret_cpp + " " + fn_name + "(" + sep.join(parts) + ");")
            if len(fn_decls) > 0:
                fwd_lines.append("namespace " + target_ns + " {")
                fwd_lines.extend(fn_decls)
                fwd_lines.append("}  // namespace " + target_ns)
        if len(fwd_lines) > 0:
            cpp_txt = inject_after_includes_block(cpp_txt, join_str_list("\n", fwd_lines))
        generated_lines_total += count_text_lines(cpp_txt)
        if max_generated_lines > 0:
            check_guard_limit(
                "emit",
                "max_generated_lines",
                generated_lines_total,
                {"max_generated_lines": max_generated_lines},
                str(mod_path),
            )
        write_text_file(cpp_path, cpp_txt)

        manifest_modules.append(
            {
                "module": mod_key,
                "label": label,
                "header": str(hdr_path),
                "source": str(cpp_path),
                "is_entry": is_entry,
            }
        )

    manifest_for_dump: dict[str, Any] = {
        "entry": entry_key,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_obj: Any = manifest_for_dump
    manifest_txt = json.dumps(manifest_obj, ensure_ascii=False, indent=2)
    generated_lines_total += count_text_lines(manifest_txt)
    if max_generated_lines > 0:
        check_guard_limit(
            "emit",
            "max_generated_lines",
            generated_lines_total,
            {"max_generated_lines": max_generated_lines},
            str(entry_path),
        )
    write_text_file(manifest_path, manifest_txt)
    return {
        "entry": entry_key,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
        "manifest": str(manifest_path),
        "generated_lines_total": generated_lines_total,
    }
