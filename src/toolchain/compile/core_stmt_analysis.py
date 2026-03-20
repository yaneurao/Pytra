#!/usr/bin/env python3
"""Shared statement analysis helpers for self-hosted EAST parsing."""

from __future__ import annotations

from typing import Any


def _sh_extract_leading_docstring(stmts: list[dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
    """先頭文が docstring の場合に抽出し、残り文リストを返す。"""
    if len(stmts) == 0:
        return None, stmts
    first = stmts[0]
    if not isinstance(first, dict) or first.get("kind") != "Expr":
        return None, stmts
    val = first.get("value")
    if not isinstance(val, dict) or val.get("kind") != "Constant":
        return None, stmts
    s = val.get("value")
    if not isinstance(s, str):
        return None, stmts
    return s, stmts[1:]


def _sh_collect_yield_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから yield 値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Yield":
            val = st.get("value")
            if isinstance(val, dict):
                t_val = val.get("resolved_type", "unknown")
                if isinstance(t_val, str) and t_val != "":
                    out.append(t_val)
                else:
                    out.append("unknown")
            else:
                out.append("None")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_yield_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_yield_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_yield_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_yield_value_types(h_body))
    return out


def _sh_collect_return_value_types(stmts: list[dict[str, Any]]) -> list[str]:
    """文リストから `return <expr>` の戻り値型を再帰収集する（入れ子関数/クラスは除外）。"""
    out: list[str] = []
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind == "Return":
            val = st.get("value")
            if not isinstance(val, dict):
                continue
            t_val_obj: Any = val.get("resolved_type")
            t_val = str(t_val_obj) if isinstance(t_val_obj, str) else "unknown"
            out.append(t_val if t_val != "" else "unknown")
            continue
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"If", "While", "For", "ForRange"}:
            body_obj: Any = st.get("body")
            body_list: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj: Any = st.get("orelse")
            orelse_list: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body_list = body_obj if isinstance(body_obj, list) else []
            out.extend(_sh_collect_return_value_types(body_list))
            orelse_obj = st.get("orelse")
            orelse_list = orelse_obj if isinstance(orelse_obj, list) else []
            out.extend(_sh_collect_return_value_types(orelse_list))
            final_obj = st.get("finalbody")
            final_list = final_obj if isinstance(final_obj, list) else []
            out.extend(_sh_collect_return_value_types(final_list))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for h in handlers:
                if not isinstance(h, dict):
                    continue
                h_body_obj: Any = h.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.extend(_sh_collect_return_value_types(h_body))
    return out


def _sh_infer_return_type_for_untyped_def(declared_ret: str, stmts: list[dict[str, Any]]) -> str:
    """戻り注釈なし（`None`）関数に対し `return <expr>` から戻り型を推定する。"""
    if declared_ret != "None":
        return declared_ret
    ret_types = _sh_collect_return_value_types(stmts)
    if len(ret_types) == 0:
        return declared_ret
    picked = ""
    for rt in ret_types:
        t = rt if rt != "" else "unknown"
        if t == "None":
            continue
        if picked == "":
            picked = t
            continue
        if picked == t:
            continue
        if picked == "unknown" or t == "unknown":
            picked = "unknown"
            continue
        picked = "Any"
        break
    if picked == "":
        return declared_ret
    return picked


def _sh_collect_store_name_ids(target: Any, out: set[str]) -> None:
    """代入ターゲットから Name 識別子を再帰収集する。"""
    if isinstance(target, dict):
        kind = str(target.get("kind", ""))
        if kind == "Name":
            name = target.get("id")
            if isinstance(name, str) and name != "":
                out.add(name)
            return
        if kind == "Starred":
            _sh_collect_store_name_ids(target.get("value"), out)
            return
        if kind in {"Tuple", "List"}:
            elems_obj: Any = target.get("elements")
            elems: list[Any] = elems_obj if isinstance(elems_obj, list) else []
            for elem in elems:
                _sh_collect_store_name_ids(elem, out)
            return
        return
    if isinstance(target, list):
        for item in target:
            _sh_collect_store_name_ids(item, out)


def _sh_collect_reassigned_names(stmts: list[dict[str, Any]]) -> set[str]:
    """文リストから再代入（再束縛）されたローカル名を収集する。"""
    out: set[str] = set()
    for st in stmts:
        if not isinstance(st, dict):
            continue
        kind = str(st.get("kind", ""))
        if kind in {"FunctionDef", "ClassDef"}:
            continue
        if kind in {"Assign", "AnnAssign", "AugAssign"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            continue
        if kind == "Swap":
            _sh_collect_store_name_ids(st.get("left"), out)
            _sh_collect_store_name_ids(st.get("right"), out)
            continue
        if kind in {"For", "ForRange"}:
            _sh_collect_store_name_ids(st.get("target"), out)
            body_obj: Any = st.get("body")
            body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj: Any = st.get("orelse")
            orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind in {"If", "While"}:
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            continue
        if kind == "Try":
            body_obj = st.get("body")
            body = body_obj if isinstance(body_obj, list) else []
            out.update(_sh_collect_reassigned_names(body))
            orelse_obj = st.get("orelse")
            orelse = orelse_obj if isinstance(orelse_obj, list) else []
            out.update(_sh_collect_reassigned_names(orelse))
            final_obj = st.get("finalbody")
            finalbody = final_obj if isinstance(final_obj, list) else []
            out.update(_sh_collect_reassigned_names(finalbody))
            handlers_obj: Any = st.get("handlers")
            handlers: list[dict[str, Any]] = handlers_obj if isinstance(handlers_obj, list) else []
            for handler in handlers:
                if not isinstance(handler, dict):
                    continue
                h_name = handler.get("name")
                if isinstance(h_name, str) and h_name != "":
                    out.add(h_name)
                h_body_obj: Any = handler.get("body")
                h_body: list[dict[str, Any]] = h_body_obj if isinstance(h_body_obj, list) else []
                out.update(_sh_collect_reassigned_names(h_body))
    return out


def _sh_build_arg_usage_map(
    arg_order: list[str],
    arg_types: dict[str, str],
    fn_stmts: list[dict[str, Any]],
) -> dict[str, str]:
    """関数本文の代入状況から `arg_usage` を構築する。"""
    usage: dict[str, str] = {}
    for arg_name in arg_types.keys():
        usage[arg_name] = "readonly"
    for arg_name in arg_order:
        usage[arg_name] = "readonly"

    reassigned = _sh_collect_reassigned_names(fn_stmts)
    for arg_name in arg_types.keys():
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    for arg_name in arg_order:
        if arg_name in reassigned:
            usage[arg_name] = "reassigned"
    return usage


def _sh_make_generator_return_type(declared_ret: str, yield_types: list[str]) -> tuple[str, str]:
    """yield 検出時の関数戻り型（list[...]）と要素型を決定する。"""
    elem = "unknown"
    if declared_ret != "" and declared_ret != "None":
        elem = declared_ret
    for yt in yield_types:
        if yt in {"", "unknown", "None"}:
            continue
        if elem == "unknown":
            elem = yt
            continue
        if elem != yt:
            elem = "Any"
            break
    return "list[" + elem + "]", elem
