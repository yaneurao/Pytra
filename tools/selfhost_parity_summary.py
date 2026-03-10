#!/usr/bin/env python3
"""Shared summary helpers for representative selfhost parity suites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParitySummaryRow:
    lane: str
    subject: str
    top_level_category: str
    detail_category: str
    note: str


def normalize_top_level_category(detail_category: str) -> str:
    if detail_category == "pass":
        return "pass"
    if detail_category == "toolchain_missing":
        return "toolchain_missing"
    if detail_category in {
        "known_block",
        "preview_only",
        "not_implemented",
        "unsupported_by_design",
        "blocked",
    }:
        return "known_block"
    return "regression"


def build_summary_row(lane: str, subject: str, detail_category: str, note: str) -> ParitySummaryRow:
    return ParitySummaryRow(
        lane=lane,
        subject=subject,
        top_level_category=normalize_top_level_category(detail_category),
        detail_category=detail_category,
        note=note,
    )


def format_summary_line(row: ParitySummaryRow) -> str:
    note = row.note.strip()
    if note == "":
        note = "-"
    return (
        f"- {row.lane}: subject={row.subject} category={row.top_level_category} "
        f"detail={row.detail_category} note={note}"
    )
