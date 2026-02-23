"""トランスパイラ CLI の共通引数定義。"""

from __future__ import annotations

from pytra.std import argparse
from pytra.std import os
from pytra.std.pathlib import Path
from pytra.std.typing import Iterable


def add_common_transpile_args(
    parser: argparse.ArgumentParser,
    *,
    enable_negative_index_mode: bool = False,
    parser_backends: Iterable[str] | None = None,
) -> None:
    """各トランスパイラで共通利用する CLI 引数を追加する。"""
    parser.add_argument("input", help="Input .py or EAST .json")
    parser.add_argument("-o", "--output", help="Output file path")
    if enable_negative_index_mode:
        parser.add_argument(
            "--negative-index-mode",
            choices=["always", "const_only", "off"],
            help="Policy for Python-style negative indexing on list/str subscripts",
        )
    if parser_backends is not None:
        choices = list(parser_backends)
        parser.add_argument(
            "--parser-backend",
            choices=choices,
            help="EAST parser backend for .py input",
        )


def normalize_common_transpile_args(
    args: argparse.Namespace,
    *,
    default_negative_index_mode: str | None = None,
    default_parser_backend: str | None = None,
) -> argparse.Namespace:
    """共通引数の既定値を埋める。"""
    if default_negative_index_mode is not None:
        cur = getattr(args, "negative_index_mode", None)
        if not cur:
            setattr(args, "negative_index_mode", default_negative_index_mode)
    if default_parser_backend is not None:
        cur = getattr(args, "parser_backend", None)
        if not cur:
            setattr(args, "parser_backend", default_parser_backend)
    return args


def join_str_list(sep: str, items: list[str]) -> str:
    """区切り文字で `list[str]` を結合する selfhost-safe helper。"""
    return sep.join(items)


def split_infix_once(text: str, sep: str) -> tuple[str, str, bool]:
    """`text` を最初の `sep` で1回だけ分割する。見つからない場合は失敗を返す。"""
    if sep == "":
        return "", "", False
    pos = text.find(sep)
    if pos >= 0:
        end = pos + len(sep)
        return text[:pos], text[end:], True
    return "", "", False


def local_binding_name(name: str, asname: str) -> str:
    """import 句のローカル束縛名を返す。"""
    if asname != "":
        return asname
    head, _tail, found = split_infix_once(name, ".")
    if found and head != "":
        return head
    return name


def split_graph_issue_entry(v_txt: str) -> tuple[str, str]:
    """`file: module` 形式を `(file, module)` へ分解する。"""
    left, right, found = split_infix_once(v_txt, ": ")
    if found:
        return left, right
    return v_txt, v_txt


def replace_first(text: str, old: str, replacement: str) -> str:
    """`text` 内の最初の `old` だけを `replacement` に置換する。"""
    pos = text.find(old)
    if pos < 0:
        return text
    return text[:pos] + replacement + text[pos + len(old) :]


def split_ws_tokens(text: str) -> list[str]:
    """空白区切りトークンへ分解する（連続空白は 1 区切り扱い）。"""
    tokens: list[str] = []
    cur = ""
    for ch in text:
        if ch == " " or ch == "\t":
            if cur != "":
                tokens.append(cur)
                cur = ""
        else:
            cur += ch
    if cur != "":
        tokens.append(cur)
    return tokens


def append_unique_non_empty(items: list[str], seen: set[str], value: str) -> None:
    """空でない文字列を未登録時のみ追加する。"""
    if value == "" or value in seen:
        return
    seen.add(value)
    items.append(value)


def split_top_level_csv(text: str) -> list[str]:
    """括弧ネストを考慮してカンマ区切りを分割する。"""
    out: list[str] = []
    cur = ""
    depth_paren = 0
    depth_brack = 0
    depth_brace = 0
    for ch in text:
        if ch == "(":
            depth_paren += 1
            cur += ch
        elif ch == ")":
            if depth_paren > 0:
                depth_paren -= 1
            cur += ch
        elif ch == "[":
            depth_brack += 1
            cur += ch
        elif ch == "]":
            if depth_brack > 0:
                depth_brack -= 1
            cur += ch
        elif ch == "{":
            depth_brace += 1
            cur += ch
        elif ch == "}":
            if depth_brace > 0:
                depth_brace -= 1
            cur += ch
        elif ch == "," and depth_paren == 0 and depth_brack == 0 and depth_brace == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        out.append(tail)
    return out


def split_type_args(text: str) -> list[str]:
    """`A[B,C[D]]` の `B,C[D]` をトップレベルで分割する。"""
    out: list[str] = []
    cur = ""
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            part: str = cur.strip()
            if part != "":
                out.append(part)
            cur = ""
        else:
            cur += ch
    tail: str = cur.strip()
    if tail != "":
        out.append(tail)
    return out


def split_top_level_union(text: str) -> list[str]:
    """`A|B[list[C|D]]` をトップレベルの `|` で分割する。"""
    out: list[str] = []
    cur = ""
    depth = 0
    for ch in text:
        if ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            if depth > 0:
                depth -= 1
            cur += ch
        elif ch == "|" and depth == 0:
            part = cur.strip()
            if part != "":
                out.append(part)
            cur = ""
        else:
            cur += ch
    tail = cur.strip()
    if tail != "":
        out.append(tail)
    return out


def path_parent_text(path_obj: Path) -> str:
    """Path から親ディレクトリ文字列を取得する。"""
    path_txt: str = str(path_obj)
    if path_txt == "":
        return "."
    last_sep = -1
    for i, ch in enumerate(path_txt):
        if ch == "/" or ch == "\\":
            last_sep = i
    if last_sep <= 0:
        return "."
    return path_txt[:last_sep]


def mkdirs_for_cli(path_txt: str) -> None:
    """CLI 出力向けに親ディレクトリを作成する。"""
    if path_txt == "":
        return
    os.makedirs(path_txt, exist_ok=True)


def write_text_file(path_obj: Path, text: str) -> None:
    """CLI 出力向けにテキストを書き出す。"""
    f = open(str(path_obj), "w", encoding="utf-8")
    f.write(text)
    f.close()


def count_text_lines(text: str) -> int:
    """テキストの行数を返す。空文字列は 0 行。"""
    if text == "":
        return 0
    count = 1
    for ch in text:
        if ch == "\n":
            count += 1
    return count


def dict_str_get(src: dict[str, str], key: str, default_value: str = "") -> str:
    """`dict[str, str]` から値を取得する（未定義時は既定値）。"""
    if key in src:
        return src[key]
    return default_value


def looks_like_runtime_function_name(name: str) -> bool:
    """ランタイム関数名（`py_*` か `ns::func`）らしい文字列か判定する。"""
    if name == "":
        return False
    if name.find("::") != -1:
        return True
    if name.startswith("py_"):
        return True
    return False


def is_pytra_module_name(module_name: str) -> bool:
    """`pytra` 配下モジュール名かを判定する。"""
    return module_name == "pytra" or module_name.startswith("pytra.")


def path_key_for_graph(p: Path) -> str:
    """依存グラフ内部で使うパス文字列キーを返す。"""
    return str(p)


def rel_disp_for_graph(base: Path, p: Path) -> str:
    """表示用に `base` からの相対パス文字列を返す。"""
    base_txt = str(base)
    p_txt = str(p)
    base_prefix = base_txt if base_txt.endswith("/") else base_txt + "/"
    if p_txt.startswith(base_prefix):
        return p_txt[len(base_prefix) :]
    if p_txt == base_txt:
        return "."
    return p_txt


def module_name_from_path_for_graph(root: Path, module_path: Path) -> str:
    """import graph 用の module_id フォールバック解決。"""
    root_txt = str(root)
    path_txt = str(module_path)
    in_root = False
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
        in_root = True
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", ".")
    if rel.endswith(".__init__"):
        rel = rel[: -9]
    if not in_root:
        stem = module_path.stem
        stem = module_path.parent.name if stem == "__init__" else stem
        rel = stem
    return rel


def module_id_from_east_for_graph(root: Path, module_path: Path, east_doc: dict[str, Any]) -> str:
    """import graph 用の EAST module_id 抽出。"""
    module_id = ""
    meta_any = east_doc.get("meta")
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str):
            module_id = module_id_any
    return module_id if module_id != "" else module_name_from_path_for_graph(root, module_path)


def graph_cycle_dfs(
    key: str,
    graph_adj: dict[str, list[str]],
    key_to_disp: dict[str, str],
    color: dict[str, int],
    stack: list[str],
    cycles: list[str],
    cycle_seen: set[str],
) -> None:
    """import graph DFS で循環参照を収集する。"""
    color[key] = 1
    stack.append(key)
    nxts: list[str] = []
    if key in graph_adj:
        nxts = graph_adj[key]
    for nxt in nxts:
        c = color.get(nxt, 0)
        if c == 0:
            graph_cycle_dfs(nxt, graph_adj, key_to_disp, color, stack, cycles, cycle_seen)
        elif c == 1:
            j = -1
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx] == nxt:
                    j = idx
                    break
            if j >= 0:
                nodes: list[str] = []
                for m in range(j, len(stack)):
                    nodes.append(stack[m])
                nodes.append(nxt)
                disp_nodes: list[str] = []
                for dk in nodes:
                    disp_nodes.append(key_to_disp.get(dk, dk))
                cycle_txt = join_str_list(" -> ", disp_nodes)
                if cycle_txt not in cycle_seen:
                    cycle_seen.add(cycle_txt)
                    cycles.append(cycle_txt)
    stack.pop()
    color[key] = 2


def resolve_user_module_path_for_graph(module_name: str, search_root: Path) -> Path:
    """import graph 用のユーザーモジュール解決（未解決は空 Path）。"""
    if module_name.startswith("pytra.") or module_name == "pytra":
        return Path("")
    rel = module_name.replace(".", "/")
    parts = module_name.split(".")
    leaf = parts[len(parts) - 1] if len(parts) > 0 else ""
    cur_dir = str(search_root)
    cur_dir = cur_dir if cur_dir != "" else "."
    seen_dirs: set[str] = set()
    best_path = ""
    best_rank = -1
    best_distance = 1000000000
    distance = 0
    while cur_dir not in seen_dirs:
        seen_dirs.add(cur_dir)
        prefix = cur_dir
        if prefix != "" and not prefix.endswith("/"):
            prefix += "/"
        cand_init = prefix + rel + "/__init__.py"
        cand_named = prefix + rel + "/" + leaf + ".py" if leaf != "" else ""
        cand_flat = prefix + rel + ".py"
        candidates: list[tuple[str, int]] = []
        candidates.append((cand_init, 3))
        if cand_named != "":
            candidates.append((cand_named, 2))
        candidates.append((cand_flat, 1))
        for path_txt, rank in candidates:
            if Path(path_txt).exists():
                if rank > best_rank or (rank == best_rank and distance < best_distance):
                    best_path = path_txt
                    best_rank = rank
                    best_distance = distance
        parent_dir = path_parent_text(Path(cur_dir))
        if parent_dir == cur_dir:
            break
        cur_dir = parent_dir if parent_dir != "" else "."
        distance += 1
    if best_path != "":
        return Path(best_path)
    return Path("")


def format_graph_list_section(out: str, label: str, items: list[str]) -> str:
    """依存解析レポートの1セクションを追記して返す。"""
    out2 = out + label + ":\n"
    if len(items) == 0:
        out2 += "  (none)\n"
        return out2
    for val_txt in items:
        out2 += "  - " + val_txt + "\n"
    return out2


def collect_import_modules(east_module: dict[str, object]) -> list[str]:
    """EAST module から import / from-import のモジュール名を抽出する。"""
    out: list[str] = []
    seen: set[str] = set()
    body_any = east_module.get("body")
    if not isinstance(body_any, list):
        return out
    for stmt_any in body_any:
        if not isinstance(stmt_any, dict):
            continue
        kind = ""
        kind_any = stmt_any.get("kind")
        if isinstance(kind_any, str):
            kind = kind_any
        if kind == "Import":
            names_any = stmt_any.get("names")
            if not isinstance(names_any, list):
                continue
            for ent_any in names_any:
                if not isinstance(ent_any, dict):
                    continue
                name_any = ent_any.get("name")
                if isinstance(name_any, str):
                    append_unique_non_empty(out, seen, name_any)
        elif kind == "ImportFrom":
            module_any = stmt_any.get("module")
            if isinstance(module_any, str):
                append_unique_non_empty(out, seen, module_any)
    return out


def is_known_non_user_import(
    module_name: str,
    runtime_std_source_root: Path,
    runtime_utils_source_root: Path,
) -> bool:
    """import graph でユーザーファイル解決不要とみなす import か判定する。"""
    if module_name == "__future__" or module_name == "os" or module_name == "glob":
        return True
    rel = module_name.replace(".", "/")
    std_root_txt = str(runtime_std_source_root)
    if std_root_txt != "" and not std_root_txt.endswith("/"):
        std_root_txt += "/"
    utils_root_txt = str(runtime_utils_source_root)
    if utils_root_txt != "" and not utils_root_txt.endswith("/"):
        utils_root_txt += "/"
    if Path(std_root_txt + rel + ".py").exists():
        return True
    if Path(std_root_txt + rel + "/__init__.py").exists():
        return True
    if Path(utils_root_txt + rel + ".py").exists():
        return True
    if Path(utils_root_txt + rel + "/__init__.py").exists():
        return True
    return False


def resolve_module_name_for_graph(
    raw_name: str,
    root_dir: Path,
    runtime_std_source_root: Path,
    runtime_utils_source_root: Path,
) -> dict[str, str]:
    """import graph 用のモジュール解決（順序依存を避ける前段 helper）。"""
    if raw_name.startswith("."):
        return {"status": "relative", "module_id": raw_name, "path": ""}
    if is_pytra_module_name(raw_name):
        return {"status": "pytra", "module_id": raw_name, "path": ""}
    dep_file = resolve_user_module_path_for_graph(raw_name, root_dir)
    if str(dep_file) != "":
        return {"status": "user", "module_id": raw_name, "path": str(dep_file)}
    if is_known_non_user_import(raw_name, runtime_std_source_root, runtime_utils_source_root):
        return {"status": "known", "module_id": raw_name, "path": ""}
    return {"status": "missing", "module_id": raw_name, "path": ""}


def resolve_codegen_options(
    preset: str,
    negative_index_mode_opt: str,
    bounds_check_mode_opt: str,
    floor_div_mode_opt: str,
    mod_mode_opt: str,
    int_width_opt: str,
    str_index_mode_opt: str,
    str_slice_mode_opt: str,
    opt_level_opt: str,
) -> tuple[str, str, str, str, str, str, str, str]:
    """プリセットと個別指定から最終オプションを決定する。"""
    neg = "const_only"
    bnd = "off"
    fdiv = "native"
    mod = "native"
    int_width = "64"
    str_index = "native"
    str_slice = "byte"
    opt_level = "3"

    if preset != "":
        if preset == "native":
            neg = "off"
            bnd = "off"
            fdiv = "native"
            mod = "native"
            int_width = "64"
            str_index = "native"
            str_slice = "byte"
            opt_level = "3"
        elif preset == "balanced":
            neg = "const_only"
            bnd = "debug"
            fdiv = "python"
            mod = "python"
            int_width = "64"
            str_index = "byte"
            str_slice = "byte"
            opt_level = "2"
        elif preset == "python":
            neg = "always"
            bnd = "always"
            fdiv = "python"
            mod = "python"
            int_width = "bigint"
            str_index = "codepoint"
            str_slice = "codepoint"
            opt_level = "0"
        else:
            raise ValueError(f"invalid --preset: {preset}")

    if negative_index_mode_opt != "":
        neg = negative_index_mode_opt
    if bounds_check_mode_opt != "":
        bnd = bounds_check_mode_opt
    if floor_div_mode_opt != "":
        fdiv = floor_div_mode_opt
    if mod_mode_opt != "":
        mod = mod_mode_opt
    if int_width_opt != "":
        int_width = int_width_opt
    if str_index_mode_opt != "":
        str_index = str_index_mode_opt
    if str_slice_mode_opt != "":
        str_slice = str_slice_mode_opt
    if opt_level_opt != "":
        opt_level = opt_level_opt
    return neg, bnd, fdiv, mod, int_width, str_index, str_slice, opt_level


def validate_codegen_options(
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
) -> str:
    """最終オプションの妥当性を検証し、エラーメッセージを返す。"""
    if negative_index_mode not in {"always", "const_only", "off"}:
        return f"invalid --negative-index-mode: {negative_index_mode}"
    if bounds_check_mode not in {"always", "debug", "off"}:
        return f"invalid --bounds-check-mode: {bounds_check_mode}"
    if floor_div_mode not in {"native", "python"}:
        return f"invalid --floor-div-mode: {floor_div_mode}"
    if mod_mode not in {"native", "python"}:
        return f"invalid --mod-mode: {mod_mode}"
    if int_width not in {"32", "64", "bigint"}:
        return f"invalid --int-width: {int_width}"
    if int_width == "bigint":
        return "--int-width=bigint is not implemented yet"
    if str_index_mode not in {"byte", "codepoint", "native"}:
        return f"invalid --str-index-mode: {str_index_mode}"
    if str_slice_mode not in {"byte", "codepoint"}:
        return f"invalid --str-slice-mode: {str_slice_mode}"
    if opt_level not in {"0", "1", "2", "3"}:
        return f"invalid -O level: {opt_level}"
    if str_index_mode == "codepoint":
        return "--str-index-mode=codepoint is not implemented yet"
    if str_slice_mode == "codepoint":
        return "--str-slice-mode=codepoint is not implemented yet"
    return ""


def dump_codegen_options_text(
    preset: str,
    negative_index_mode: str,
    bounds_check_mode: str,
    floor_div_mode: str,
    mod_mode: str,
    int_width: str,
    str_index_mode: str,
    str_slice_mode: str,
    opt_level: str,
) -> str:
    """解決済みオプションを人間向けテキストへ整形する。"""
    p = preset if preset != "" else "(none)"
    out = "options:\n"
    out += f"  preset: {p}\n"
    out += f"  negative-index-mode: {negative_index_mode}\n"
    out += f"  bounds-check-mode: {bounds_check_mode}\n"
    out += f"  floor-div-mode: {floor_div_mode}\n"
    out += f"  mod-mode: {mod_mode}\n"
    out += f"  int-width: {int_width}\n"
    out += f"  str-index-mode: {str_index_mode}\n"
    out += f"  str-slice-mode: {str_slice_mode}\n"
    out += f"  opt-level: {opt_level}\n"
    return out


def sort_str_list_copy(items: list[str]) -> list[str]:
    """`list[str]` を昇順へ整列したコピーを返す（selfhost-safe 実装）。"""
    out: list[str] = []
    for item in items:
        out.append(item)
    for i in range(1, len(out)):
        key = out[i]
        insert_at = i
        for j in range(i - 1, -1, -1):
            if out[j] > key:
                out[j + 1] = out[j]
                insert_at = j
            else:
                break
        out[insert_at] = key
    return out


def empty_parse_dict() -> dict[str, str]:
    out: dict[str, str] = {}
    out["__error"] = ""
    return out


def _parse_error_dict(msg: str) -> dict[str, str]:
    out = empty_parse_dict()
    out["__error"] = msg
    return out


def parse_py2cpp_argv(argv: list[str]) -> dict[str, str]:
    """py2cpp 向け CLI 引数を解析し、値辞書（`__error` 含む）を返す。"""
    out: dict[str, str] = {
        "input": "",
        "output": "",
        "output_dir": "",
        "top_namespace_opt": "",
        "negative_index_mode_opt": "",
        "bounds_check_mode_opt": "",
        "floor_div_mode_opt": "",
        "mod_mode_opt": "",
        "int_width_opt": "",
        "str_index_mode_opt": "",
        "str_slice_mode_opt": "",
        "opt_level_opt": "",
        "preset": "",
        "parser_backend": "self_hosted",
        "guard_profile": "default",
        "max_ast_depth": "",
        "max_parse_nodes": "",
        "max_symbols_per_module": "",
        "max_scope_depth": "",
        "max_import_graph_nodes": "",
        "max_import_graph_edges": "",
        "max_generated_lines": "",
        "no_main": "0",
        "single_file": "0",
        "output_mode_explicit": "0",
        "dump_deps": "0",
        "dump_options": "0",
        "header_output": "",
        "emit_runtime_cpp": "0",
        "help": "0",
        "__error": "",
    }
    i = 0
    while i < len(argv):
        a = str(argv[i])
        if a == "-h" or a == "--help":
            out["help"] = "1"
        elif a == "-o" or a == "--output":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --output")
            out["output"] = argv[i]
        elif a == "--negative-index-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --negative-index-mode")
            out["negative_index_mode_opt"] = argv[i]
        elif a == "--output-dir":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --output-dir")
            out["output_dir"] = argv[i]
        elif a == "--single-file":
            out["single_file"] = "1"
            out["output_mode_explicit"] = "1"
        elif a == "--multi-file":
            out["single_file"] = "0"
            out["output_mode_explicit"] = "1"
        elif a == "--top-namespace":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --top-namespace")
            out["top_namespace_opt"] = argv[i]
        elif a == "--bounds-check-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --bounds-check-mode")
            out["bounds_check_mode_opt"] = argv[i]
        elif a == "--floor-div-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --floor-div-mode")
            out["floor_div_mode_opt"] = argv[i]
        elif a == "--mod-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --mod-mode")
            out["mod_mode_opt"] = argv[i]
        elif a == "--int-width":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --int-width")
            out["int_width_opt"] = argv[i]
        elif a == "--str-index-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --str-index-mode")
            out["str_index_mode_opt"] = argv[i]
        elif a == "--str-slice-mode":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --str-slice-mode")
            out["str_slice_mode_opt"] = argv[i]
        elif a in {"-O0", "-O1", "-O2", "-O3"}:
            out["opt_level_opt"] = a[2:]
        elif a == "-O":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for -O")
            out["opt_level_opt"] = argv[i]
        elif a == "--opt-level":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --opt-level")
            out["opt_level_opt"] = argv[i]
        elif a == "--preset":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --preset")
            out["preset"] = argv[i]
        elif a == "--parser-backend":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --parser-backend")
            out["parser_backend"] = argv[i]
        elif a == "--guard-profile":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --guard-profile")
            out["guard_profile"] = argv[i]
        elif a == "--max-ast-depth":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-ast-depth")
            out["max_ast_depth"] = argv[i]
        elif a == "--max-parse-nodes":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-parse-nodes")
            out["max_parse_nodes"] = argv[i]
        elif a == "--max-symbols-per-module":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-symbols-per-module")
            out["max_symbols_per_module"] = argv[i]
        elif a == "--max-scope-depth":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-scope-depth")
            out["max_scope_depth"] = argv[i]
        elif a == "--max-import-graph-nodes":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-import-graph-nodes")
            out["max_import_graph_nodes"] = argv[i]
        elif a == "--max-import-graph-edges":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-import-graph-edges")
            out["max_import_graph_edges"] = argv[i]
        elif a == "--max-generated-lines":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --max-generated-lines")
            out["max_generated_lines"] = argv[i]
        elif a == "--no-main":
            out["no_main"] = "1"
        elif a == "--dump-deps":
            out["dump_deps"] = "1"
        elif a == "--dump-options":
            out["dump_options"] = "1"
        elif a == "--header-output":
            i += 1
            if i >= len(argv):
                return _parse_error_dict("missing value for --header-output")
            out["header_output"] = argv[i]
        elif a == "--emit-runtime-cpp":
            out["emit_runtime_cpp"] = "1"
        elif a.startswith("-"):
            return _parse_error_dict(f"unknown option: {a}")
        else:
            if out["input"] == "":
                out["input"] = a
            elif out["output"] == "":
                # `py2cpp.py INPUT.py OUTPUT.cpp` 形式も受け付ける。
                out["output"] = a
            else:
                return _parse_error_dict(f"unexpected extra argument: {a}")
        i += 1
    return out
