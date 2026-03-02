"""Rust backend lower stage (EAST3 -> RustIR)."""

from __future__ import annotations

from .east3_to_rs_ir import lower_east3_to_rs_ir

__all__ = ["lower_east3_to_rs_ir"]
