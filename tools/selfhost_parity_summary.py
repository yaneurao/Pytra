#!/usr/bin/env python3
"""Shared summary helpers for representative selfhost parity suites."""

from __future__ import annotations

from dataclasses import dataclass

from src.toolchain.compiler.backend_registry_diagnostics import KNOWN_BLOCK_DETAIL_CATEGORIES
from src.toolchain.compiler.backend_registry_diagnostics import infer_diagnostic_detail_from_text
from src.toolchain.compiler.backend_registry_diagnostics import normalize_top_level_category


@dataclass(frozen=True)
class ParitySummaryRow:
    lane: str
    subject: str
    top_level_category: str
    detail_category: str
    note: str


def build_summary_row(lane: str, subject: str, detail_category: str, note: str) -> ParitySummaryRow:
    return ParitySummaryRow(
        lane=lane,
        subject=subject,
        top_level_category=normalize_top_level_category(detail_category),
        detail_category=detail_category,
        note=note,
    )


def classify_known_block_detail(note: str) -> str | None:
    inferred = infer_diagnostic_detail_from_text(note)
    if inferred in KNOWN_BLOCK_DETAIL_CATEGORIES:
        return inferred
    return None


def build_direct_e2e_summary_row(subject: str, status: str, note: str) -> ParitySummaryRow:
    known_block_detail = classify_known_block_detail(note)
    if status == "pass":
        detail = "pass"
    elif status == "selfhost_transpile_fail" and known_block_detail is not None:
        detail = known_block_detail
    elif status == "stdout_fail":
        detail = "direct_parity_fail"
    elif status == "compile_fail":
        detail = "direct_compile_fail"
    elif status == "run_fail":
        detail = "direct_run_fail"
    elif status == "selfhost_transpile_fail":
        detail = "sample_transpile_fail"
    elif status == "python_run_fail":
        detail = "python_run_fail"
    elif status == "build_selfhost_fail":
        detail = "build_fail"
    elif status in {"missing_selfhost_binary", "missing_source"}:
        detail = "missing_output"
    else:
        detail = "regression"
    return build_summary_row("direct_e2e", subject, detail, note)


def build_stage2_summary_row(subject: str, status: str, note: str) -> ParitySummaryRow:
    if status == "pass":
        detail = "pass"
    elif status == "build_fail":
        detail = "stage2_build_fail"
    elif status == "diff_fail":
        detail = "stage2_diff_fail"
    elif status == "missing_binary":
        detail = "missing_output"
    elif status == "verify_fail":
        detail = "direct_parity_fail"
    else:
        detail = "regression"
    return build_summary_row("stage2", subject, detail, note)


def build_stage2_diff_summary_row(subject: str, status: str, note: str) -> ParitySummaryRow:
    known_block_detail = classify_known_block_detail(note)
    if status == "pass":
        detail = "pass"
    elif status == "selfhost_not_implemented":
        detail = "not_implemented"
    elif status in {"selfhost_transpile_fail", "host_transpile_fail"} and known_block_detail is not None:
        detail = known_block_detail
    elif status == "bridge_json_unavailable":
        detail = "blocked"
    elif status == "known_diff":
        detail = "known_block"
    elif status == "artifact_diff":
        detail = "stage2_diff_fail"
    elif status == "selfhost_transpile_fail":
        detail = "stage2_transpile_fail"
    elif status in {"missing_output", "missing_binary"}:
        detail = "missing_output"
    elif status == "host_transpile_fail":
        detail = "host_transpile_fail"
    elif status == "east3_contract_fail":
        detail = "east3_contract_fail"
    else:
        detail = "regression"
    return build_summary_row("stage2_diff", subject, detail, note)


def format_summary_line(row: ParitySummaryRow) -> str:
    note = row.note.strip()
    if note == "":
        note = "-"
    return (
        f"- {row.lane}: subject={row.subject} category={row.top_level_category} "
        f"detail={row.detail_category} note={note}"
    )


def render_summary_block(title: str, rows: list[ParitySummaryRow], *, skip_pass: bool) -> list[str]:
    filtered = [row for row in rows if not (skip_pass and row.top_level_category == "pass")]
    if len(filtered) == 0 and len(rows) != 0:
        filtered = [build_summary_row(title, "all", "pass", "")]
    if len(filtered) == 0:
        return []
    return [f"[{title} summary]", *[format_summary_line(row) for row in filtered]]


def print_summary_block(title: str, rows: list[ParitySummaryRow], *, skip_pass: bool) -> None:
    for line in render_summary_block(title, rows, skip_pass=skip_pass):
        print(line)
