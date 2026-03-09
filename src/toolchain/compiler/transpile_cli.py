"""Compatibility shim for transpile CLI helpers.

Canonical implementation moved to ``toolchain.frontends.transpile_cli``.
"""

from __future__ import annotations

from toolchain.compiler.typed_boundary import CompilerRootDocument
from toolchain.frontends import transpile_cli as _front
from toolchain.frontends.transpile_cli import *  # noqa: F401,F403


normalize_east1_to_east2_document_stage = _front.normalize_east1_to_east2_document_stage
load_east1_document_stage = _front.load_east1_document_stage
load_east3_document_stage = _front.load_east3_document_stage


def normalize_east1_to_east2_document(east_doc):
    stage_fn = globals().get("normalize_east1_to_east2_document_stage")
    if callable(stage_fn):
        out = stage_fn(east_doc)
        if isinstance(out, dict):
            return out
    return _front.normalize_east1_to_east2_document(east_doc)


def load_east1_document(input_path, parser_backend="self_hosted"):
    stage_fn = globals().get("load_east1_document_stage")
    if callable(stage_fn):
        return stage_fn(
            input_path,
            parser_backend=parser_backend,
            load_east_document_fn=load_east_document,
        )
    return _front.load_east1_document(input_path, parser_backend=parser_backend)


def load_east3_document(
    input_path,
    parser_backend="self_hosted",
    object_dispatch_mode="",
    east3_opt_level=1,
    east3_opt_pass="",
    dump_east3_before_opt="",
    dump_east3_after_opt="",
    dump_east3_opt_trace="",
    target_lang="",
):
    stage_fn = globals().get("load_east3_document_stage")
    if callable(stage_fn):
        return stage_fn(
            input_path,
            parser_backend=parser_backend,
            object_dispatch_mode=object_dispatch_mode,
            east3_opt_level=east3_opt_level,
            east3_opt_pass=east3_opt_pass,
            dump_east3_before_opt=dump_east3_before_opt,
            dump_east3_after_opt=dump_east3_after_opt,
            dump_east3_opt_trace=dump_east3_opt_trace,
            target_lang=target_lang,
            load_east_document_fn=load_east_document,
            make_user_error_fn=make_user_error,
        )
    return _front.load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )


def load_east3_document_typed(
    input_path,
    parser_backend="self_hosted",
    object_dispatch_mode="",
    east3_opt_level=1,
    east3_opt_pass="",
    dump_east3_before_opt="",
    dump_east3_after_opt="",
    dump_east3_opt_trace="",
    target_lang="",
) -> CompilerRootDocument:
    return _front.load_east3_document_typed(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )
