"""EAST3 stage helpers."""

from __future__ import annotations

from toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3
from toolchain.compile.east3_optimizer import optimize_east3_document
from toolchain.compile.east3_optimizer import render_east3_opt_trace
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_template import validate_template_module
from toolchain.frontends.type_expr import sync_type_expr_mirrors
from pytra.std import json
from pytra.std.pathlib import Path
from typing import Any
from toolchain.json_adapters import dumps_object as _json_dumps_object


def lower_east2_to_east3_document(
    east2_doc: dict[str, object],
    object_dispatch_mode: str = "",
) -> dict[str, object]:
    """公開委譲: `EAST2 -> EAST3` lower を実行する。"""
    out_any = lower_east2_to_east3(east2_doc, object_dispatch_mode=object_dispatch_mode)
    if isinstance(out_any, dict):
        out_doc: dict[str, object] = out_any
        return out_doc
    raise RuntimeError("EAST3 root must be a dict")


def _module_id_from_doc_or_path(doc: dict[str, object], input_path: Path) -> str:
    meta_any = doc.get("meta")
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str) and module_id_any.strip() != "":
            return module_id_any.strip()
    file_name = input_path.name
    for suffix in (".east3.json", ".json", ".py"):
        if file_name.endswith(suffix):
            file_name = file_name[: -len(suffix)]
            break
    file_name = file_name.replace("-", "_").strip()
    if file_name == "":
        raise RuntimeError("failed to infer module_id from path: " + str(input_path))
    return file_name


def _resolve_dispatch_mode(doc: dict[str, object], override: str) -> str:
    if override in ("native", "type_id"):
        return override
    meta_any = doc.get("meta")
    if isinstance(meta_any, dict):
        dispatch_mode_any = meta_any.get("dispatch_mode")
        if dispatch_mode_any in ("native", "type_id"):
            return str(dispatch_mode_any)
    return "native"


def _normalize_legacy_source_spans(value: object) -> None:
    if isinstance(value, dict):
        d: dict[str, Any] = value
        span_any = d.get("source_span")
        if isinstance(span_any, dict):
            sd: dict[str, Any] = span_any
            has_legacy = "lineno" in sd and "col" in sd and "end_lineno" in sd and "end_col" in sd
            has_canonical = "lineno" in sd and "col_offset" in sd and "end_lineno" in sd and "end_col_offset" in sd
            if has_legacy and not has_canonical:
                lineno = sd.get("lineno")
                col = sd.get("col")
                end_lineno = sd.get("end_lineno")
                end_col = sd.get("end_col")
                if (
                    type(lineno) is int
                    and type(col) is int
                    and type(end_lineno) is int
                    and type(end_col) is int
                ):
                    d["source_span"] = {
                        "lineno": lineno,
                        "col_offset": col,
                        "end_lineno": end_lineno,
                        "end_col_offset": end_col,
                    }
                elif lineno is None and col is None and end_lineno is None and end_col is None:
                    d.pop("source_span", None)
        for child in d.values():
            _normalize_legacy_source_spans(child)
    elif isinstance(value, list):
        vl: list[object] = value
        for child in vl:
            _normalize_legacy_source_spans(child)


def _validate_raw_east3_via_link(
    doc: dict[str, object],
    *,
    expected_dispatch_mode: str,
    module_id: str,
    require_source_spans: bool = False,
) -> dict[str, object]:
    # Use the public link facade without reintroducing a link<->ir import cycle at module init time.
    from toolchain.link import validate_raw_east3_doc

    return validate_raw_east3_doc(
        doc,
        expected_dispatch_mode=expected_dispatch_mode,
        module_id=module_id,
        require_source_spans=require_source_spans,
    )


def expand_mixin_bases(east_doc: dict[str, object]) -> dict[str, object]:
    """Expand mixin bases: copy methods and class members from mixin classes into target class.

    For each ClassDef that has ``mixin_bases``, the pass copies FunctionDef and
    AnnAssign/Assign nodes from each mixin class body into the target class body
    (skipping members that already exist in the target).  After expansion the
    ``mixin_bases`` key is removed so downstream stages see only single inheritance.
    """
    body_any = east_doc.get("body")
    if not isinstance(body_any, list):
        return east_doc
    body: list[object] = body_any

    # 1. Build class_name -> ClassDef node map.
    class_map: dict[str, dict[str, object]] = {}
    for item in body:
        if isinstance(item, dict):
            d_item: dict[str, object] = item
            if d_item.get("kind") == "ClassDef":
                name_any = d_item.get("name")
                if isinstance(name_any, str):
                    class_map[name_any] = d_item

    # 2. For each ClassDef with mixin_bases, expand.
    for item in body:
        if not isinstance(item, dict):
            continue
        cls_item: dict[str, object] = item
        if cls_item.get("kind") != "ClassDef":
            continue
        mixin_bases_any = cls_item.get("mixin_bases")
        if not isinstance(mixin_bases_any, list) or len(mixin_bases_any) == 0:
            continue

        target_body_any = cls_item.get("body")
        if not isinstance(target_body_any, list):
            continue
        target_body: list[object] = target_body_any

        # Collect existing member names in the target class.
        existing_names: set[str] = set()
        for stmt in target_body:
            if isinstance(stmt, dict):
                sd: dict[str, object] = stmt
                stmt_kind = sd.get("kind")
                if stmt_kind == "FunctionDef":
                    fn_name = sd.get("name")
                    if isinstance(fn_name, str):
                        existing_names.add(fn_name)
                elif stmt_kind == "AnnAssign" or stmt_kind == "Assign":
                    tgt = sd.get("target")
                    if isinstance(tgt, dict):
                        tgt_d: dict[str, object] = tgt
                        if tgt_d.get("kind") == "Name":
                            tgt_id = tgt_d.get("id")
                            if isinstance(tgt_id, str):
                                existing_names.add(tgt_id)

        # Copy from each mixin (in order).
        target_field_types_any = cls_item.get("field_types")
        target_field_types: dict[str, object] = target_field_types_any if isinstance(target_field_types_any, dict) else {}
        mixin_list: list[object] = mixin_bases_any
        for mixin_name in mixin_list:
            if not isinstance(mixin_name, str):
                continue
            mixin_cls = class_map.get(mixin_name)
            if mixin_cls is None:
                continue
            mixin_body_any = mixin_cls.get("body")
            if not isinstance(mixin_body_any, list):
                continue
            for mixin_stmt in mixin_body_any:
                if not isinstance(mixin_stmt, dict):
                    continue
                ms: dict[str, object] = mixin_stmt
                mixin_kind = ms.get("kind")
                member_name: str | None = None
                if mixin_kind == "FunctionDef":
                    fn_name = ms.get("name")
                    if isinstance(fn_name, str):
                        member_name = fn_name
                elif mixin_kind == "AnnAssign" or mixin_kind == "Assign":
                    tgt = ms.get("target")
                    if isinstance(tgt, dict):
                        tgt_d2: dict[str, object] = tgt
                        if tgt_d2.get("kind") == "Name":
                            tgt_id = tgt_d2.get("id")
                            if isinstance(tgt_id, str):
                                member_name = tgt_id
                else:
                    continue
                if member_name is not None and member_name not in existing_names:
                    import copy
                    target_body.append(copy.deepcopy(ms))
                    existing_names.add(member_name)
            # Also merge field_types from the mixin.
            mixin_field_types_any = mixin_cls.get("field_types")
            if isinstance(mixin_field_types_any, dict):
                mft: dict[str, object] = mixin_field_types_any
                for ft_name, ft_type in mft.items():
                    if ft_name not in target_field_types:
                        target_field_types[ft_name] = ft_type
        if isinstance(target_field_types_any, dict):
            cls_item["field_types"] = target_field_types

        # Remove mixin_bases so downstream sees single inheritance only.
        cls_item.pop("mixin_bases", None)

    return east_doc


def load_east3_document(
    input_path: Path,
    parser_backend: str = "self_hosted",
    object_dispatch_mode: str = "",
    east3_opt_level: str | int | object = 1,
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
    target_lang: str = "",
    load_east_document_fn: Any = None,
    make_user_error_fn: Any = None,
) -> dict[str, object]:
    """入力ファイルを読み込み、`EAST2 -> EAST3` lower を適用して返す。"""
    if load_east_document_fn is None:
        raise RuntimeError("load_east_document_fn is required")
    east2_any = load_east_document_fn(input_path, parser_backend=parser_backend)
    if isinstance(east2_any, dict):
        east2_doc: dict[str, object] = east2_any
        east2_doc = expand_mixin_bases(east2_doc)
        east3_doc = lower_east2_to_east3_document(east2_doc, object_dispatch_mode=object_dispatch_mode)
        _normalize_legacy_source_spans(east3_doc)
        east3_doc = _validate_raw_east3_via_link(
            east3_doc,
            expected_dispatch_mode=_resolve_dispatch_mode(east3_doc, object_dispatch_mode),
            module_id=_module_id_from_doc_or_path(east3_doc, input_path),
            require_source_spans=False,
        )
        if dump_east3_before_opt != "":
            before_path = Path(dump_east3_before_opt)
            before_path.parent.mkdir(parents=True, exist_ok=True)
            before_path.write_text(_json_dumps_object(east3_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        optimized_doc, report = optimize_east3_document(
            east3_doc,
            opt_level=east3_opt_level,
            target_lang=target_lang,
            opt_pass_spec=east3_opt_pass,
        )
        if dump_east3_after_opt != "":
            after_path = Path(dump_east3_after_opt)
            after_path.parent.mkdir(parents=True, exist_ok=True)
            after_path.write_text(_json_dumps_object(optimized_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if dump_east3_opt_trace != "":
            trace_path = Path(dump_east3_opt_trace)
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_text(render_east3_opt_trace(report), encoding="utf-8")
        sync_type_expr_mirrors(optimized_doc)
        _normalize_legacy_source_spans(optimized_doc)
        optimized_doc = _validate_raw_east3_via_link(
            optimized_doc,
            expected_dispatch_mode=_resolve_dispatch_mode(optimized_doc, object_dispatch_mode),
            module_id=_module_id_from_doc_or_path(optimized_doc, input_path),
            require_source_spans=False,
        )
        return validate_template_module(validate_runtime_abi_module(optimized_doc))
    if callable(make_user_error_fn):
        raise make_user_error_fn(
            "input_invalid",
            "Failed to build EAST3.",
            ["EAST3 root must be a dict."],
        )
    raise RuntimeError("Failed to build EAST3.")
