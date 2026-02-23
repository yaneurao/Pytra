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


def make_user_error(category: str, summary: str, details: list[str]) -> Exception:
    """共通フォーマットの user error 例外を生成する。"""
    payload = "__PYTRA_USER_ERROR__|" + category + "|" + summary
    for detail in details:
        payload += "\n" + detail
    return RuntimeError(payload)


def parse_user_error(err_text: str) -> dict[str, object]:
    """共通フォーマットの user error 文字列を解析する。"""
    text = err_text
    tag = "__PYTRA_USER_ERROR__|"
    if not text.startswith(tag):
        return {"category": "", "summary": "", "details": []}
    lines: list[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
        else:
            cur += ch
    lines.append(cur)
    head = lines[0] if len(lines) > 0 else ""
    parts: list[str] = []
    cur = ""
    split_count = 0
    for ch in head:
        if ch == "|" and split_count < 2:
            parts.append(cur)
            cur = ""
            split_count += 1
        else:
            cur += ch
    parts.append(cur)
    if len(parts) != 3:
        return {"category": "", "summary": "", "details": []}
    category = parts[1]
    summary = parts[2]
    details: list[str] = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line != "":
            details.append(line)
    return {"category": category, "summary": summary, "details": details}


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


def inject_after_includes_block(cpp_text: str, block: str) -> str:
    """先頭 include 群の直後に block を差し込む。"""
    if block == "":
        return cpp_text
    pos = cpp_text.find("\n\n")
    if pos < 0:
        return cpp_text + "\n" + block + "\n"
    head = cpp_text[: pos + 2]
    tail = cpp_text[pos + 2 :]
    return head + block + "\n" + tail


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


def first_import_detail_line(source_text: str, kind: str) -> str:
    """import エラー表示向けに、入力コードから該当 import 行を抜き出す。"""
    lines = source_text.splitlines()
    for i in range(len(lines)):
        raw = lines[i]
        line = raw if isinstance(raw, str) else ""
        hash_pos = line.find("#")
        if hash_pos >= 0:
            line = line[:hash_pos]
        line = line.strip()
        if line == "":
            continue
        if kind == "wildcard":
            if line.startswith("from ") and " import " in line and line.endswith("*"):
                parts = split_ws_tokens(line)
                if len(parts) >= 4 and parts[0] == "from" and parts[2] == "import" and parts[3] == "*":
                    return "from " + parts[1] + " import *"
        if kind == "relative":
            if line.startswith("from .") and " import " in line:
                parts = split_ws_tokens(line)
                if len(parts) >= 4 and parts[0] == "from" and parts[2] == "import":
                    return "from " + parts[1] + " import " + parts[3]
    if kind == "wildcard":
        return "from ... import *"
    return "from .module import symbol"


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


def normalize_param_annotation(ann: str) -> str:
    """関数引数注釈文字列を EAST 互換の粗い型名へ正規化する。"""
    t = ann.strip()
    if t == "":
        return "unknown"
    if "Any" in t:
        return "Any"
    if "object" in t:
        return "object"
    if t in {"int", "float", "str", "bool", "bytes", "bytearray"}:
        return t
    if t.startswith("list[") or t.startswith("dict[") or t.startswith("set[") or t.startswith("tuple["):
        return t
    return t


def extract_function_signatures_from_python_source(src_path: Path) -> dict[str, dict[str, list[str]]]:
    """`def` シグネチャから引数型とデフォルト値（テキスト）を抽出する。"""
    text = ""
    try:
        text = src_path.read_text(encoding="utf-8")
    except Exception:
        empty: dict[str, dict[str, list[str]]] = {}
        return empty
    lines: list[str] = text.splitlines()
    sig_map: dict[str, dict[str, list[str]]] = {}
    skip_until = 0
    for i in range(len(lines)):
        if i < skip_until:
            continue
        line = lines[i]
        stripped = line.strip()
        if (len(line) - len(line.lstrip(" "))) == 0 and stripped.startswith("def "):
            sig_text = stripped
            j = i + 1
            for k in range(i + 1, len(lines)):
                if sig_text.endswith(":"):
                    break
                sig_text += " " + lines[k].strip()
                j = k + 1
            skip_until = j
            if not sig_text.endswith(":"):
                continue
            sig0 = sig_text[:-1].strip()
            if not sig0.startswith("def "):
                continue
            p0 = sig0.find("(")
            if p0 < 0:
                continue
            name = sig0[4:p0].strip()
            if name == "":
                continue
            depth = 0
            p1 = -1
            for k in range(p0, len(sig0)):
                ch = sig0[k : k + 1]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        p1 = k
                        break
            if p1 < 0:
                continue
            params = sig0[p0 + 1 : p1]
            arg_types: list[str] = []
            arg_defaults: list[str] = []
            parts = split_top_level_csv(params)
            for part in parts:
                prm = part.strip()
                if prm == "" or prm.startswith("*"):
                    continue
                default_txt = ""
                eq_top = prm.find("=")
                if eq_top >= 0:
                    default_txt = prm[eq_top + 1 :].strip()
                    prm = prm[:eq_top].strip()
                colon = prm.find(":")
                if colon < 0:
                    arg_types.append("unknown")
                    arg_defaults.append(default_txt)
                    continue
                ann = prm[colon + 1 :]
                arg_types.append(normalize_param_annotation(ann))
                arg_defaults.append(default_txt)
            sig_map[name] = {
                "arg_types": arg_types,
                "arg_defaults": arg_defaults,
            }
    return sig_map


def extract_function_arg_types_from_python_source(src_path: Path) -> dict[str, list[str]]:
    """EAST 化に失敗するモジュール用の関数シグネチャ簡易抽出。"""
    sigs = extract_function_signatures_from_python_source(src_path)
    out: dict[str, list[str]] = {}
    for fn_name_obj, sig_obj in sigs.items():
        if not isinstance(fn_name_obj, str):
            continue
        if not isinstance(sig_obj, dict):
            continue
        arg_types_obj = sig_obj.get("arg_types")
        if isinstance(arg_types_obj, list):
            out[fn_name_obj] = arg_types_obj
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


def python_module_exists_under(root_dir: Path, module_tail: str) -> bool:
    """`root_dir` 配下に `module_tail` 相当の `.py` / package があるかを返す。"""
    if module_tail == "":
        return False
    root_txt = str(root_dir)
    root_txt = root_txt[:-1] if root_txt.endswith("/") else root_txt
    rel = module_tail.replace(".", "/")
    mod_py = Path(root_txt + "/" + rel + ".py")
    if mod_py.exists():
        return True
    pkg_init = Path(root_txt + "/" + rel + "/__init__.py")
    if pkg_init.exists():
        return True
    return False


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


def dict_any_get(src: dict[str, object], key: str) -> object | None:
    """`dict[str, object]` から値を取得する（未定義時は `None`）。"""
    if key in src:
        return src[key]
    return None


def dict_any_get_str(src: dict[str, object], key: str, default_value: str = "") -> str:
    """`dict[str, object]` から `str` 値を取得する（未定義/非文字列は既定値）。"""
    if key in src:
        value = src[key]
        if isinstance(value, str):
            return value
    return default_value


def dict_any_kind(src: dict[str, object]) -> str:
    """EAST 風ノード辞書の `kind` を返す（未定義時は空文字）。"""
    return dict_any_get_str(src, "kind")


def name_target_id(target: dict[str, object]) -> str:
    """代入先が Name ノードのとき識別子を返す。"""
    if dict_any_kind(target) != "Name":
        return ""
    return dict_any_get_str(target, "id")


def stmt_target_name(stmt: dict[str, object]) -> str:
    """文ノードの `target` から Name 識別子を取得する。"""
    return name_target_id(dict_any_get_dict(stmt, "target"))


def stmt_assigned_names(stmt: dict[str, object]) -> list[str]:
    """Assign/AnnAssign 文の Name 代入先を抽出する。"""
    kind = dict_any_kind(stmt)
    out: list[str] = []
    if kind == "Assign":
        for tgt_obj in assign_targets(stmt):
            name_txt = name_target_id(tgt_obj)
            if name_txt != "":
                out.append(name_txt)
    elif kind == "AnnAssign":
        name_txt = stmt_target_name(stmt)
        if name_txt != "":
            out.append(name_txt)
    return out


def stmt_child_stmt_lists(stmt: dict[str, object]) -> list[list[dict[str, object]]]:
    """文ノードが持つ子 statement list 群を抽出する。"""
    out: list[list[dict[str, object]]] = []
    body = dict_any_get_dict_list(stmt, "body")
    if len(body) > 0:
        out.append(body)
    orelse = dict_any_get_dict_list(stmt, "orelse")
    if len(orelse) > 0:
        out.append(orelse)
    finalbody = dict_any_get_dict_list(stmt, "finalbody")
    if len(finalbody) > 0:
        out.append(finalbody)
    handlers = dict_any_get_dict_list(stmt, "handlers")
    for handler in handlers:
        h_body = dict_any_get_dict_list(handler, "body")
        if len(h_body) > 0:
            out.append(h_body)
    cases = dict_any_get_dict_list(stmt, "cases")
    for case in cases:
        c_body = dict_any_get_dict_list(case, "body")
        if len(c_body) > 0:
            out.append(c_body)
    return out


def collect_store_names_from_target(target: dict[str, object], out: set[str]) -> None:
    """代入先 target から束縛名を抽出する。"""
    kind = dict_any_kind(target)
    if kind == "Name":
        ident = dict_any_get_str(target, "id")
        if ident != "":
            out.add(ident)
        return
    if kind == "Tuple" or kind == "List":
        for ent in dict_any_get_dict_list(target, "elements"):
            collect_store_names_from_target(ent, out)


def stmt_list_parse_metrics(body: list[dict[str, object]], depth: int) -> tuple[int, int]:
    """statement list から `parse_nodes` と `max_depth` を計測する。"""
    node_count = 0
    max_depth = 0
    if len(body) > 0:
        max_depth = depth
    for st in body:
        node_count += 1
        if depth > max_depth:
            max_depth = depth
        for child in stmt_child_stmt_lists(st):
            child_nodes, child_depth = stmt_list_parse_metrics(child, depth + 1)
            node_count += child_nodes
            if child_depth > max_depth:
                max_depth = child_depth
    return node_count, max_depth


def module_parse_metrics(east_module: dict[str, object]) -> dict[str, int]:
    """EAST module 単位の parse 指標（深さ・ノード数）を返す。"""
    body = dict_any_get_dict_list(east_module, "body")
    node_count, max_depth = stmt_list_parse_metrics(body, 1)
    module_nodes = node_count + 1  # Module root
    module_depth = max_depth if max_depth > 0 else 1
    return {"max_ast_depth": module_depth, "parse_nodes": module_nodes}


def collect_symbols_from_stmt(stmt: dict[str, object]) -> set[str]:
    """statement ノードの束縛名を抽出して返す。"""
    symbols: set[str] = set()
    kind = dict_any_kind(stmt)
    if kind == "FunctionDef" or kind == "AsyncFunctionDef":
        fn_name = dict_any_get_str(stmt, "name")
        if fn_name != "":
            symbols.add(fn_name)
        for arg_any in dict_any_get_list(stmt, "arg_order"):
            if isinstance(arg_any, str) and arg_any != "":
                symbols.add(arg_any)
    elif kind == "ClassDef":
        cls_name = dict_any_get_str(stmt, "name")
        if cls_name != "":
            symbols.add(cls_name)
    elif kind == "Assign" or kind == "AnnAssign":
        for name_txt in stmt_assigned_names(stmt):
            if name_txt != "":
                symbols.add(name_txt)
    elif kind == "For":
        target = dict_any_get_dict(stmt, "target")
        if len(target) > 0:
            collect_store_names_from_target(target, symbols)
    elif kind == "With":
        for item in dict_any_get_dict_list(stmt, "items"):
            opt_vars = dict_any_get_dict(item, "optional_vars")
            if len(opt_vars) > 0:
                collect_store_names_from_target(opt_vars, symbols)
    elif kind == "ExceptHandler":
        name_txt = dict_any_get_str(stmt, "name")
        if name_txt != "":
            symbols.add(name_txt)
    elif kind == "Import":
        for ent in dict_any_get_dict_list(stmt, "names"):
            name_txt = dict_any_get_str(ent, "name")
            asname_txt = dict_any_get_str(ent, "asname")
            local_name = local_binding_name(name_txt, asname_txt)
            if local_name != "":
                symbols.add(local_name)
    elif kind == "ImportFrom":
        for ent in dict_any_get_dict_list(stmt, "names"):
            sym_name = dict_any_get_str(ent, "name")
            if sym_name == "*":
                continue
            asname_txt = dict_any_get_str(ent, "asname")
            local_name = local_binding_name(sym_name, asname_txt)
            if local_name != "":
                symbols.add(local_name)
    return symbols


def collect_symbols_from_stmt_list(body: list[dict[str, object]]) -> set[str]:
    """statement list から束縛名を再帰収集する。"""
    symbols: set[str] = set()
    for st in body:
        for name_txt in collect_symbols_from_stmt(st):
            symbols.add(name_txt)
        for child in stmt_child_stmt_lists(st):
            for name_txt in collect_symbols_from_stmt_list(child):
                symbols.add(name_txt)
    return symbols


def module_analyze_metrics(
    east_module: dict[str, object],
    scope_nesting_kinds: set[str],
) -> dict[str, int]:
    """EAST module 単位の analyze 指標（symbol 数・scope 深さ）を返す。"""
    body = dict_any_get_dict_list(east_module, "body")
    symbols = collect_symbols_from_stmt_list(body)
    scope_depth = stmt_list_scope_depth(body, 0, scope_nesting_kinds)
    return {"symbols": len(symbols), "scope_depth": scope_depth}


def select_guard_module_map(
    input_txt: str,
    east_module: dict[str, object],
    module_east_map_cache: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """ガード計測対象の module map を返す。"""
    if len(module_east_map_cache) > 0:
        return module_east_map_cache
    key = input_txt if input_txt != "" else "<input>"
    return {key: east_module}


def check_parse_stage_guards(
    module_map: dict[str, dict[str, object]],
    guard_limits: dict[str, int],
) -> None:
    """parse ステージの AST 深さ / ノード数ガードを検証する。"""
    parse_nodes_total = 0
    for mod_key, east in module_map.items():
        metrics = module_parse_metrics(east)
        module_depth = metrics["max_ast_depth"] if "max_ast_depth" in metrics else 0
        module_nodes = metrics["parse_nodes"] if "parse_nodes" in metrics else 0
        check_guard_limit("parse", "max_ast_depth", module_depth, guard_limits, mod_key)
        parse_nodes_total += module_nodes
    check_guard_limit("parse", "max_parse_nodes", parse_nodes_total, guard_limits)


def check_analyze_stage_guards(
    module_map: dict[str, dict[str, object]],
    import_graph_analysis: dict[str, object],
    guard_limits: dict[str, int],
    scope_nesting_kinds: set[str],
) -> None:
    """analyze ステージの symbol/scope/import graph ガードを検証する。"""
    for mod_key, east in module_map.items():
        metrics = module_analyze_metrics(east, scope_nesting_kinds)
        symbol_count = metrics["symbols"] if "symbols" in metrics else 0
        scope_depth = metrics["scope_depth"] if "scope_depth" in metrics else 0
        check_guard_limit("analyze", "max_symbols_per_module", symbol_count, guard_limits, mod_key)
        check_guard_limit("analyze", "max_scope_depth", scope_depth, guard_limits, mod_key)
    graph_nodes = len(dict_any_get_str_list(import_graph_analysis, "user_module_files"))
    graph_edges = len(dict_any_get_str_list(import_graph_analysis, "edges"))
    check_guard_limit("analyze", "max_import_graph_nodes", graph_nodes, guard_limits)
    check_guard_limit("analyze", "max_import_graph_edges", graph_edges, guard_limits)


def module_export_table(
    module_east_map: dict[str, dict[str, object]],
    root: Path,
) -> dict[str, set[str]]:
    """ユーザーモジュールの公開シンボル表（関数/クラス/代入名）を構築する。"""
    out: dict[str, set[str]] = {}
    for mod_key, east in module_east_map.items():
        mod_path = Path(mod_key)
        mod_name = module_id_from_east_for_graph(root, mod_path, east)
        if mod_name == "":
            continue
        body = dict_any_get_dict_list(east, "body")
        exports: set[str] = set()
        for st in body:
            kind = dict_any_kind(st)
            if kind == "FunctionDef" or kind == "ClassDef":
                name_txt = dict_any_get_str(st, "name")
                if name_txt != "":
                    exports.add(name_txt)
            elif kind == "Assign" or kind == "AnnAssign":
                for name_txt in stmt_assigned_names(st):
                    exports.add(name_txt)
        out[mod_name] = exports
    return out


def build_module_type_schema(module_east_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """モジュール間共有用の最小型スキーマ（関数/クラス）を構築する。"""
    out: dict[str, dict[str, Any]] = {}
    for mod_path, east in module_east_map.items():
        body = dict_any_get_dict_list(east, "body")
        fn_schema: dict[str, dict[str, Any]] = {}
        cls_schema: dict[str, dict[str, Any]] = {}
        for st in body:
            kind = dict_any_kind(st)
            if kind == "FunctionDef":
                name_txt = dict_any_get_str(st, "name")
                if name_txt != "":
                    arg_types = dict_any_get_dict(st, "arg_types")
                    arg_order = dict_any_get_list(st, "arg_order")
                    ret_type = dict_any_get_str(st, "return_type", "None")
                    fn_ent: dict[str, Any] = {
                        "arg_types": arg_types,
                        "arg_order": arg_order,
                        "return_type": ret_type,
                    }
                    fn_schema[name_txt] = fn_ent
            elif kind == "ClassDef":
                name_txt = dict_any_get_str(st, "name")
                if name_txt != "":
                    fields = dict_any_get_dict(st, "field_types")
                    cls_schema[name_txt] = {"field_types": fields}
        out[mod_path] = {"functions": fn_schema, "classes": cls_schema}
    return out


def validate_from_import_symbols_or_raise(
    module_east_map: dict[str, dict[str, object]],
    root: Path,
) -> None:
    """`from M import S` の `S` が `M` の公開シンボルに存在するか検証する。"""
    exports = module_export_table(module_east_map, root)
    if len(exports) == 0:
        return
    details: list[str] = []
    for mod_key, east in module_east_map.items():
        file_disp = rel_disp_for_graph(root, Path(mod_key))
        body = dict_any_get_dict_list(east, "body")
        for st in body:
            if dict_any_kind(st) == "ImportFrom":
                imported_mod = dict_any_get_str(st, "module")
                if imported_mod in exports:
                    names = dict_any_get_dict_list(st, "names")
                    for ent in names:
                        sym = dict_any_get_str(ent, "name")
                        if sym == "*":
                            continue
                        if sym != "" and sym not in exports[imported_mod]:
                            details.append(
                                f"kind=missing_symbol file={file_disp} import=from {imported_mod} import {sym}"
                            )
    if len(details) > 0:
        raise make_user_error(
            "input_invalid",
            "Failed to resolve imports (missing symbols).",
            details,
        )


def set_import_module_binding(import_modules: dict[str, str], local_name: str, module_id: str) -> None:
    """import module alias 束縛を追加する。"""
    if module_id == "":
        return
    import_modules[local_name] = module_id


def set_import_symbol_binding(
    import_symbols: dict[str, dict[str, str]],
    local_name: str,
    module_id: str,
    symbol: str,
) -> None:
    """import symbol alias 束縛を追加する。"""
    if module_id == "" or symbol == "":
        return
    import_symbols[local_name] = {"module": module_id, "name": symbol}


def set_import_symbol_binding_and_module_set(
    import_symbols: dict[str, dict[str, str]],
    import_symbol_modules: set[str],
    local_name: str,
    module_id: str,
    symbol: str,
) -> None:
    """import symbol alias 束縛を追加し、参照 module を追跡する。"""
    if module_id == "" or symbol == "":
        return
    import_symbols[local_name] = {"module": module_id, "name": symbol}
    import_symbol_modules.add(module_id)


def stmt_list_scope_depth(
    body: list[dict[str, object]],
    depth: int,
    scope_nesting_kinds: set[str],
) -> int:
    """statement list の最大 scope 深さを返す。"""
    max_depth = depth
    for st in body:
        kind = dict_any_kind(st)
        child_depth = depth + 1 if kind in scope_nesting_kinds else depth
        if child_depth > max_depth:
            max_depth = child_depth
        for child in stmt_child_stmt_lists(st):
            d = stmt_list_scope_depth(child, child_depth, scope_nesting_kinds)
            if d > max_depth:
                max_depth = d
    return max_depth


def dict_any_get_str_list(src: dict[str, object], key: str) -> list[str]:
    """`dict[str, object]` の list 値から `str` 要素だけを抽出する。"""
    out: list[str] = []
    if key not in src:
        return out
    value = src[key]
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, str):
            out.append(item)
    return out


def dict_any_get_list(src: dict[str, object], key: str) -> list[object]:
    """`dict[str, object]` から list 値を取得する（非 list は空）。"""
    if key not in src:
        return []
    value = src[key]
    if isinstance(value, list):
        return value
    return []


def dict_any_get_dict(src: dict[str, object], key: str) -> dict[str, object]:
    """`dict[str, object]` から dict 値を取得する（非 dict は空）。"""
    if key not in src:
        return {}
    value = src[key]
    if isinstance(value, dict):
        return value
    return {}


def dict_any_get_dict_list(src: dict[str, object], key: str) -> list[dict[str, object]]:
    """`dict[str, object]` の list 値から dict 要素だけを抽出する。"""
    out: list[dict[str, object]] = []
    if key not in src:
        return out
    value = src[key]
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


def assign_targets(stmt: dict[str, object]) -> list[dict[str, object]]:
    """Assign/AnnAssign 互換で代入先 target 群を正規化して返す。"""
    targets = dict_any_get_dict_list(stmt, "targets")
    if len(targets) > 0:
        return targets
    tgt = dict_any_get_dict(stmt, "target")
    if len(tgt) > 0:
        return [tgt]
    return []


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


def sanitize_module_label(text: str) -> str:
    """モジュール識別子向けに英数字/`_` のみ残す。"""
    out_chars: list[str] = []
    for ch in text:
        ok = ((ch >= "a" and ch <= "z") or (ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9") or ch == "_")
        if ok:
            out_chars.append(ch)
        else:
            out_chars.append("_")
    out = "".join(out_chars)
    out = out if out != "" else "module"
    if out[0] >= "0" and out[0] <= "9":
        out = "_" + out
    return out


def module_rel_label(root: Path, module_path: Path) -> str:
    """`root` からの相対パスを multi-file 用モジュールラベルへ変換する。"""
    root_txt = str(root)
    path_txt = str(module_path)
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", "__")
    return sanitize_module_label(rel)


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


def meta_import_bindings(east_module: dict[str, object]) -> list[dict[str, str]]:
    """EAST `meta.import_bindings` を正規化して返す（無い場合は空）。"""
    out: list[dict[str, str]] = []
    meta_any = east_module.get("meta")
    if not isinstance(meta_any, dict):
        return out
    items_any = meta_any.get("import_bindings")
    if not isinstance(items_any, list):
        return out
    for item_any in items_any:
        if not isinstance(item_any, dict):
            continue
        module_id = ""
        module_id_any = item_any.get("module_id")
        if isinstance(module_id_any, str):
            module_id = module_id_any
        export_name = ""
        export_name_any = item_any.get("export_name")
        if isinstance(export_name_any, str):
            export_name = export_name_any
        local_name = ""
        local_name_any = item_any.get("local_name")
        if isinstance(local_name_any, str):
            local_name = local_name_any
        binding_kind = ""
        binding_kind_any = item_any.get("binding_kind")
        if isinstance(binding_kind_any, str):
            binding_kind = binding_kind_any
        if module_id != "" and local_name != "" and binding_kind in {"module", "symbol", "wildcard"}:
            entry: dict[str, str] = {}
            entry["module_id"] = module_id
            entry["export_name"] = export_name
            entry["local_name"] = local_name
            entry["binding_kind"] = binding_kind
            out.append(entry)
    return out


def meta_qualified_symbol_refs(east_module: dict[str, object]) -> list[dict[str, str]]:
    """EAST `meta.qualified_symbol_refs` を正規化して返す（無い場合は空）。"""
    out: list[dict[str, str]] = []
    meta_any = east_module.get("meta")
    if not isinstance(meta_any, dict):
        return out
    items_any = meta_any.get("qualified_symbol_refs")
    if not isinstance(items_any, list):
        return out
    for item_any in items_any:
        if not isinstance(item_any, dict):
            continue
        module_id = ""
        module_id_any = item_any.get("module_id")
        if isinstance(module_id_any, str):
            module_id = module_id_any
        symbol = ""
        symbol_any = item_any.get("symbol")
        if isinstance(symbol_any, str):
            symbol = symbol_any
        local_name = ""
        local_name_any = item_any.get("local_name")
        if isinstance(local_name_any, str):
            local_name = local_name_any
        if module_id != "" and symbol != "" and local_name != "":
            entry: dict[str, str] = {}
            entry["module_id"] = module_id
            entry["symbol"] = symbol
            entry["local_name"] = local_name
            out.append(entry)
    return out


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


def collect_reserved_import_conflicts(root: Path) -> list[str]:
    """予約名 `pytra` と衝突するユーザーファイルを収集する。"""
    out: list[str] = []
    pytra_file = root / "pytra.py"
    pytra_pkg_init = root / "pytra" / "__init__.py"
    if pytra_file.exists():
        out.append(str(pytra_file))
    if pytra_pkg_init.exists():
        out.append(str(pytra_pkg_init))
    return out


def format_graph_list_section(out: str, label: str, items: list[str]) -> str:
    """依存解析レポートの1セクションを追記して返す。"""
    out2 = out + label + ":\n"
    if len(items) == 0:
        out2 += "  (none)\n"
        return out2
    for val_txt in items:
        out2 += "  - " + val_txt + "\n"
    return out2


def dump_deps_text(east_module: dict[str, object]) -> str:
    """EAST の import メタデータを人間向けテキストへ整形する。"""
    import_bindings = meta_import_bindings(east_module)
    body = dict_any_get_dict_list(east_module, "body")
    modules: list[str] = []
    module_seen: set[str] = set()
    symbols: list[str] = []
    symbol_seen: set[str] = set()

    if len(import_bindings) > 0:
        for ent in import_bindings:
            append_unique_non_empty(modules, module_seen, ent["module_id"])
            if ent["binding_kind"] == "symbol" and ent["export_name"] != "":
                label = ent["module_id"] + "." + ent["export_name"]
                if ent["local_name"] != "" and ent["local_name"] != ent["export_name"]:
                    label += " as " + ent["local_name"]
                append_unique_non_empty(symbols, symbol_seen, label)
    else:
        for stmt_dict in body:
            kind = dict_any_kind(stmt_dict)
            if kind == "Import":
                for ent_dict in dict_any_get_dict_list(stmt_dict, "names"):
                    mod_name = dict_any_get_str(ent_dict, "name")
                    append_unique_non_empty(modules, module_seen, mod_name)
            elif kind == "ImportFrom":
                mod_name = dict_any_get_str(stmt_dict, "module")
                append_unique_non_empty(modules, module_seen, mod_name)
                for ent_dict in dict_any_get_dict_list(stmt_dict, "names"):
                    sym_name = dict_any_get_str(ent_dict, "name")
                    alias = dict_any_get_str(ent_dict, "asname")
                    if sym_name != "":
                        label = mod_name + "." + sym_name
                        if alias != "":
                            label += " as " + alias
                        append_unique_non_empty(symbols, symbol_seen, label)

    out = "modules:\n"
    if len(modules) == 0:
        out += "  (none)\n"
    else:
        for mod_name in modules:
            out += "  - " + mod_name + "\n"
    out += "symbols:\n"
    if len(symbols) == 0:
        out += "  (none)\n"
    else:
        for sym_name in symbols:
            out += "  - " + sym_name + "\n"
    return out


def format_import_graph_report(analysis: dict[str, object]) -> str:
    """依存解析結果を `--dump-deps` 向けテキストへ整形する。"""
    edges = dict_any_get_str_list(analysis, "edges")
    out = "graph:\n"
    if len(edges) == 0:
        out += "  (none)\n"
    else:
        for item in edges:
            out += "  - " + item + "\n"
    cycles = dict_any_get_str_list(analysis, "cycles")
    out = format_graph_list_section(out, "cycles", cycles)
    missing = dict_any_get_str_list(analysis, "missing_modules")
    out = format_graph_list_section(out, "missing", missing)
    relative = dict_any_get_str_list(analysis, "relative_imports")
    out = format_graph_list_section(out, "relative", relative)
    reserved = dict_any_get_str_list(analysis, "reserved_conflicts")
    out = format_graph_list_section(out, "reserved", reserved)
    return out


def validate_import_graph_or_raise(analysis: dict[str, object]) -> None:
    """依存解析の重大問題を `input_invalid` として報告する。"""
    details: list[str] = []
    for v in dict_any_get_str_list(analysis, "reserved_conflicts"):
        if v != "":
            details.append(f"kind=reserved_conflict file={v} import=pytra")
    for v_txt in dict_any_get_str_list(analysis, "relative_imports"):
        if v_txt == "":
            continue
        file_part, mod_part = split_graph_issue_entry(v_txt)
        details.append(f"kind=unsupported_import_form file={file_part} import=from {mod_part} import ...")
    for v_txt in dict_any_get_str_list(analysis, "missing_modules"):
        if v_txt == "":
            continue
        file_part, mod_part = split_graph_issue_entry(v_txt)
        details.append(f"kind=missing_module file={file_part} import={mod_part}")
    for v in dict_any_get_str_list(analysis, "cycles"):
        if v != "":
            details.append(f"kind=import_cycle file=(graph) import={v}")
    if len(details) > 0:
        raise make_user_error(
            "input_invalid",
            "Failed to resolve imports (missing/conflict/cycle).",
            details,
        )


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


def collect_user_module_files_for_graph(visited_order: list[str], key_to_path: dict[str, Path]) -> list[str]:
    """import graph 解析済みキー列と path map からソート済みファイル一覧を返す。"""
    out: list[str] = []
    visited_keys: list[str] = []
    for visited_key in visited_order:
        visited_keys.append(visited_key)
    visited_keys = sort_str_list_copy(visited_keys)
    for key in visited_keys:
        if key in key_to_path:
            out.append(str(key_to_path[key]))
    return out


def parse_guard_limit_or_raise(raw: str, option_name: str) -> int:
    """個別 `--max-*` 値を正整数へ変換する。"""
    if raw == "":
        return -1
    if not raw.isdigit():
        raise ValueError("invalid value for --" + option_name + ": " + raw)
    value = int(raw)
    if value <= 0:
        raise ValueError("invalid value for --" + option_name + ": must be > 0")
    return value


def guard_profile_base_limits(profile: str) -> dict[str, int]:
    """`off/default/strict` からガード上限初期値を解決する。"""
    out: dict[str, int] = {}
    if profile == "off":
        out["max_ast_depth"] = 0
        out["max_parse_nodes"] = 0
        out["max_symbols_per_module"] = 0
        out["max_scope_depth"] = 0
        out["max_import_graph_nodes"] = 0
        out["max_import_graph_edges"] = 0
        out["max_generated_lines"] = 0
        return out
    if profile == "default":
        out["max_ast_depth"] = 800
        out["max_parse_nodes"] = 2000000
        out["max_symbols_per_module"] = 200000
        out["max_scope_depth"] = 400
        out["max_import_graph_nodes"] = 5000
        out["max_import_graph_edges"] = 20000
        out["max_generated_lines"] = 2000000
        return out
    if profile == "strict":
        out["max_ast_depth"] = 200
        out["max_parse_nodes"] = 200000
        out["max_symbols_per_module"] = 20000
        out["max_scope_depth"] = 120
        out["max_import_graph_nodes"] = 1000
        out["max_import_graph_edges"] = 4000
        out["max_generated_lines"] = 300000
        return out
    raise ValueError("invalid --guard-profile: " + profile)


def resolve_guard_limits(
    guard_profile: str,
    max_ast_depth_raw: str,
    max_parse_nodes_raw: str,
    max_symbols_per_module_raw: str,
    max_scope_depth_raw: str,
    max_import_graph_nodes_raw: str,
    max_import_graph_edges_raw: str,
    max_generated_lines_raw: str,
) -> dict[str, int]:
    """profile + 個別指定からガード上限を解決する。"""
    profile = guard_profile if guard_profile != "" else "default"
    if profile not in {"off", "default", "strict"}:
        raise ValueError("invalid --guard-profile: " + profile)
    out = guard_profile_base_limits(profile)
    max_ast_depth = parse_guard_limit_or_raise(max_ast_depth_raw, "max-ast-depth")
    if max_ast_depth > 0:
        out["max_ast_depth"] = max_ast_depth
    max_parse_nodes = parse_guard_limit_or_raise(max_parse_nodes_raw, "max-parse-nodes")
    if max_parse_nodes > 0:
        out["max_parse_nodes"] = max_parse_nodes
    max_symbols_per_module = parse_guard_limit_or_raise(max_symbols_per_module_raw, "max-symbols-per-module")
    if max_symbols_per_module > 0:
        out["max_symbols_per_module"] = max_symbols_per_module
    max_scope_depth = parse_guard_limit_or_raise(max_scope_depth_raw, "max-scope-depth")
    if max_scope_depth > 0:
        out["max_scope_depth"] = max_scope_depth
    max_import_graph_nodes = parse_guard_limit_or_raise(max_import_graph_nodes_raw, "max-import-graph-nodes")
    if max_import_graph_nodes > 0:
        out["max_import_graph_nodes"] = max_import_graph_nodes
    max_import_graph_edges = parse_guard_limit_or_raise(max_import_graph_edges_raw, "max-import-graph-edges")
    if max_import_graph_edges > 0:
        out["max_import_graph_edges"] = max_import_graph_edges
    max_generated_lines = parse_guard_limit_or_raise(max_generated_lines_raw, "max-generated-lines")
    if max_generated_lines > 0:
        out["max_generated_lines"] = max_generated_lines
    return out


def raise_guard_limit_exceeded(
    stage: str,
    limit_key: str,
    value: int,
    max_value: int,
    detail_subject: str = "",
) -> None:
    """ガード上限超過を `input_invalid(kind=limit_exceeded, ...)` で報告する。"""
    limit_labels: dict[str, str] = {
        "max_ast_depth": "max-ast-depth",
        "max_parse_nodes": "max-parse-nodes",
        "max_symbols_per_module": "max-symbols-per-module",
        "max_scope_depth": "max-scope-depth",
        "max_import_graph_nodes": "max-import-graph-nodes",
        "max_import_graph_edges": "max-import-graph-edges",
        "max_generated_lines": "max-generated-lines",
    }
    limit_label = limit_labels[limit_key] if limit_key in limit_labels else limit_key
    detail = f"kind=limit_exceeded stage={stage} limit={limit_label} value={value} max={max_value}"
    if detail_subject != "":
        detail += " file=" + detail_subject
    raise make_user_error(
        "input_invalid",
        "Input exceeds configured guard limits.",
        [detail],
    )


def check_guard_limit(
    stage: str,
    limit_key: str,
    value: int,
    limits: dict[str, int],
    detail_subject: str = "",
) -> None:
    """`limits` に設定された上限を超えた場合に例外を送出する。"""
    max_value = limits[limit_key] if limit_key in limits else 0
    if max_value > 0 and value > max_value:
        raise_guard_limit_exceeded(stage, limit_key, value, max_value, detail_subject)


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
