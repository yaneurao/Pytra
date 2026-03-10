"""EAST3 stage helpers."""

from __future__ import annotations

from toolchain.ir.east2_to_east3_lowering import lower_east2_to_east3
from toolchain.ir.east3_optimizer import optimize_east3_document
from toolchain.ir.east3_optimizer import render_east3_opt_trace
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_template import validate_template_module
from toolchain.frontends.type_expr import sync_type_expr_mirrors
from toolchain.link.program_validator import validate_raw_east3_doc
from pytra.std import json
from pytra.std.pathlib import Path
from typing import Any


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
        span_any = value.get("source_span")
        if isinstance(span_any, dict):
            legacy_keys = ("lineno", "col", "end_lineno", "end_col")
            canonical_keys = ("lineno", "col_offset", "end_lineno", "end_col_offset")
            if all(key in span_any for key in legacy_keys) and not all(key in span_any for key in canonical_keys):
                lineno = span_any.get("lineno")
                col = span_any.get("col")
                end_lineno = span_any.get("end_lineno")
                end_col = span_any.get("end_col")
                if (
                    type(lineno) is int
                    and type(col) is int
                    and type(end_lineno) is int
                    and type(end_col) is int
                ):
                    value["source_span"] = {
                        "lineno": lineno,
                        "col_offset": col,
                        "end_lineno": end_lineno,
                        "end_col_offset": end_col,
                    }
                elif lineno is None and col is None and end_lineno is None and end_col is None:
                    value.pop("source_span", None)
        for child in value.values():
            _normalize_legacy_source_spans(child)
    elif isinstance(value, list):
        for child in value:
            _normalize_legacy_source_spans(child)


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
        east3_doc = lower_east2_to_east3_document(east2_doc, object_dispatch_mode=object_dispatch_mode)
        _normalize_legacy_source_spans(east3_doc)
        east3_doc = validate_raw_east3_doc(
            east3_doc,
            expected_dispatch_mode=_resolve_dispatch_mode(east3_doc, object_dispatch_mode),
            module_id=_module_id_from_doc_or_path(east3_doc, input_path),
            require_source_spans=False,
        )
        if dump_east3_before_opt != "":
            before_path = Path(dump_east3_before_opt)
            before_path.parent.mkdir(parents=True, exist_ok=True)
            before_path.write_text(json.dumps(east3_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        optimized_doc, report = optimize_east3_document(
            east3_doc,
            opt_level=east3_opt_level,
            target_lang=target_lang,
            opt_pass_spec=east3_opt_pass,
        )
        if dump_east3_after_opt != "":
            after_path = Path(dump_east3_after_opt)
            after_path.parent.mkdir(parents=True, exist_ok=True)
            after_path.write_text(json.dumps(optimized_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if dump_east3_opt_trace != "":
            trace_path = Path(dump_east3_opt_trace)
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_text(render_east3_opt_trace(report), encoding="utf-8")
        sync_type_expr_mirrors(optimized_doc)
        _normalize_legacy_source_spans(optimized_doc)
        optimized_doc = validate_raw_east3_doc(
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
