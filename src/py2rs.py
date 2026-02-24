#!/usr/bin/env python3
"""EAST -> Rust transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.emitter.rs_emitter import load_rs_profile, transpile_to_rust
from pytra.compiler.transpile_cli import (
    add_common_transpile_args,
    load_east3_document,
    load_east_document_compat,
)
from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys


def _make_compat_call(name: str, args: list[Any], resolved_type: str = "") -> dict[str, Any]:
    call: dict[str, Any] = {
        "kind": "Call",
        "func": {"kind": "Name", "id": name},
        "args": args,
        "keywords": [],
    }
    if resolved_type != "":
        call["resolved_type"] = resolved_type
    return call


def _legacy_target_from_plan(plan_node: Any) -> dict[str, Any]:
    if not isinstance(plan_node, dict):
        return {"kind": "Name", "id": "_"}
    kind = str(plan_node.get("kind"))
    if kind == "NameTarget":
        return {"kind": "Name", "id": str(plan_node.get("id", "_"))}
    if kind == "TupleTarget":
        elements_obj = plan_node.get("elements")
        elements_raw: list[Any] = elements_obj if isinstance(elements_obj, list) else []
        elements: list[dict[str, Any]] = []
        for elem in elements_raw:
            elements.append(_legacy_target_from_plan(elem))
        return {"kind": "Tuple", "elements": elements}
    if kind == "ExprTarget":
        target_any = plan_node.get("target")
        if isinstance(target_any, dict):
            return target_any
    return {"kind": "Name", "id": "_"}


def _type_id_expr_to_type_ref(expr: Any) -> Any:
    if not isinstance(expr, dict):
        return expr
    if str(expr.get("kind", "")) != "Name":
        return expr
    name = str(expr.get("id", ""))
    type_map: dict[str, str] = {
        "PYTRA_TID_BOOL": "bool",
        "PYTRA_TID_INT": "int",
        "PYTRA_TID_FLOAT": "float",
        "PYTRA_TID_STR": "str",
        "PYTRA_TID_LIST": "list",
        "PYTRA_TID_DICT": "dict",
        "PYTRA_TID_SET": "set",
        "PYTRA_TID_TUPLE": "tuple",
        "PYTRA_TID_OBJECT": "object",
    }
    if name in type_map:
        return {"kind": "Name", "id": type_map[name]}
    return {"kind": "Name", "id": name}


def _normalize_east3_to_legacy(node: Any) -> Any:
    if isinstance(node, list):
        out_list: list[Any] = []
        for item in node:
            out_list.append(_normalize_east3_to_legacy(item))
        return out_list
    if not isinstance(node, dict):
        return node

    kind = str(node.get("kind", ""))
    out: dict[str, Any] = {}
    for key, value in node.items():
        out[key] = _normalize_east3_to_legacy(value)

    if kind == "Module":
        out["east_stage"] = 2
        return out
    if kind == "Box":
        return out.get("value")
    if kind == "Unbox":
        return out.get("value")
    if kind == "ObjBool":
        return _make_compat_call("bool", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjLen":
        return _make_compat_call("len", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjStr":
        return _make_compat_call("str", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjIterInit":
        return _make_compat_call("iter", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "ObjIterNext":
        return _make_compat_call("next", [out.get("iter")], str(out.get("resolved_type", "")))
    if kind == "ObjTypeId":
        return _make_compat_call("py_runtime_type_id", [out.get("value")], str(out.get("resolved_type", "")))
    if kind == "IsInstance":
        expected_ref = _type_id_expr_to_type_ref(out.get("expected_type_id"))
        return _make_compat_call(
            "isinstance",
            [out.get("value"), expected_ref],
            str(out.get("resolved_type", "")),
        )
    if kind == "IsSubclass":
        return _make_compat_call(
            "py_issubclass",
            [out.get("actual_type_id"), out.get("expected_type_id")],
            str(out.get("resolved_type", "")),
        )
    if kind == "IsSubtype":
        return _make_compat_call(
            "py_is_subtype",
            [out.get("actual_type_id"), out.get("expected_type_id")],
            str(out.get("resolved_type", "")),
        )
    if kind == "ForCore":
        iter_plan = out.get("iter_plan")
        target_plan = out.get("target_plan")
        body_obj = out.get("body")
        orelse_obj = out.get("orelse")
        body: list[dict[str, Any]] = body_obj if isinstance(body_obj, list) else []
        orelse: list[dict[str, Any]] = orelse_obj if isinstance(orelse_obj, list) else []
        target = _legacy_target_from_plan(target_plan)
        target_type = ""
        if isinstance(target_plan, dict):
            target_type = str(target_plan.get("target_type", ""))
        if isinstance(iter_plan, dict):
            plan_kind = str(iter_plan.get("kind", ""))
            if plan_kind == "StaticRangeForPlan":
                return {
                    "kind": "ForRange",
                    "target": target,
                    "target_type": target_type,
                    "start": iter_plan.get("start"),
                    "stop": iter_plan.get("stop"),
                    "step": iter_plan.get("step"),
                    "range_mode": str(iter_plan.get("range_mode", "ascending")),
                    "body": body,
                    "orelse": orelse,
                }
            if plan_kind == "RuntimeIterForPlan":
                return {
                    "kind": "For",
                    "target": target,
                    "target_type": target_type,
                    "iter_mode": "runtime_protocol",
                    "iter": iter_plan.get("iter_expr"),
                    "body": body,
                    "orelse": orelse,
                }
    return out


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
) -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    if east_stage == "3":
        doc3 = load_east3_document(
            input_path,
            parser_backend=parser_backend,
            object_dispatch_mode=object_dispatch_mode,
        )
        return _normalize_east3_to_legacy(doc3)
    if east_stage == "2":
        doc2 = load_east_document_compat(input_path, parser_backend=parser_backend)
        return doc2
    raise RuntimeError("invalid east_stage: " + east_stage)


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.rs` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".rs"
    elif out.endswith(".json"):
        out = out[:-5] + ".rs"
    else:
        out = out + ".rs"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Pytra EAST -> Rust transpiler")
    add_common_transpile_args(parser, parser_backends=["self_hosted"])
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    parser.add_argument(
        "--object-dispatch-mode",
        choices=["native", "type_id"],
        help="Object boundary dispatch mode used by EAST2->EAST3 lowering",
    )
    args = parser.parse_args()
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_path = Path(output_text) if output_text != "" else _default_output_path(input_path)
    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"
    east_stage = _arg_get_str(args, "east_stage")
    if east_stage == "":
        east_stage = "3"
    object_dispatch_mode = _arg_get_str(args, "object_dispatch_mode")
    if object_dispatch_mode == "":
        object_dispatch_mode = "native"
    if east_stage == "2":
        print("warning: --east-stage 2 is compatibility mode; default is 3.", file=sys.stderr)

    east = load_east(
        input_path,
        parser_backend=parser_backend,
        east_stage=east_stage,
        object_dispatch_mode=object_dispatch_mode,
    )
    rust_src = transpile_to_rust(east)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
