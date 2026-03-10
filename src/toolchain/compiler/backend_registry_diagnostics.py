"""Shared diagnostic vocabulary for backend registry and parity reports."""

from __future__ import annotations


KNOWN_BLOCK_DETAIL_CATEGORIES = frozenset(
    {
        "known_block",
        "preview_only",
        "not_implemented",
        "unsupported_by_design",
        "blocked",
    }
)

TOOLCHAIN_MISSING_DETAIL_CATEGORIES = frozenset({"toolchain_missing"})


def normalize_top_level_category(detail_category: str) -> str:
    if detail_category == "pass":
        return "pass"
    if detail_category in TOOLCHAIN_MISSING_DETAIL_CATEGORIES:
        return "toolchain_missing"
    if detail_category in KNOWN_BLOCK_DETAIL_CATEGORIES:
        return "known_block"
    return "regression"


def unsupported_target_message(target: str) -> str:
    return "unsupported target: " + target


def unsupported_target_profile_message(target: str) -> str:
    return "unsupported target profile: " + target


def unsupported_noncpp_build_target_message(target: str) -> str:
    return "unsupported non-cpp build target: " + target


def unsupported_runtime_hook_key_message(runtime_key: str) -> str:
    return "unsupported runtime hook key: " + runtime_key


def unsupported_program_writer_key_message(writer_key: str) -> str:
    return "unsupported program writer key: " + writer_key


def unsupported_backend_symbol_ref_message(symbol_ref: str) -> str:
    return "unsupported backend symbol ref: " + symbol_ref


def unsupported_emit_kind_message(emit_kind: str) -> str:
    return "unsupported emit kind: " + emit_kind


def unsupported_runtime_hook_kind_message(runtime_key: str) -> str:
    return "unsupported runtime hook kind: " + runtime_key


def infer_diagnostic_detail_from_text(text: str) -> str | None:
    if text == "":
        return None
    text_lc = text.strip().lower()
    if text_lc == "":
        return None
    if "[not_implemented]" in text_lc or "not_implemented" in text_lc:
        return "not_implemented"
    if "[unsupported_by_design]" in text_lc or "unsupported_by_design" in text_lc:
        return "unsupported_by_design"
    if "preview backend" in text_lc or "preview-only" in text_lc or "preview only" in text_lc:
        return "preview_only"
    if "プレビュー出力" in text or "todo: 専用" in text_lc:
        return "preview_only"
    if "toolchain missing" in text_lc or text_lc.endswith("not found"):
        return "toolchain_missing"
    if "unsupported target:" in text_lc or "unsupported target profile:" in text_lc:
        return "unsupported_by_design"
    if "unsupported non-cpp build target:" in text_lc:
        return "unsupported_by_design"
    if text_lc.startswith("unsupported backend symbol ref:"):
        return "regression"
    if text_lc.startswith("unsupported runtime hook key:"):
        return "regression"
    if text_lc.startswith("unsupported program writer key:"):
        return "regression"
    if text_lc.startswith("unsupported emit kind:"):
        return "regression"
    if text_lc.startswith("unsupported runtime hook kind:"):
        return "regression"
    return None


def classify_registry_diagnostic_detail(message: str) -> str:
    inferred = infer_diagnostic_detail_from_text(message)
    if inferred is not None:
        return inferred
    return "regression"


def classify_registry_diagnostic(message: str) -> tuple[str, str]:
    detail = classify_registry_diagnostic_detail(message)
    return normalize_top_level_category(detail), detail
