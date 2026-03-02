"""Rust backend optimizer stage (RustIR -> RustIR)."""

from __future__ import annotations

from .pipeline import optimize_rs_ir

__all__ = ["optimize_rs_ir"]
