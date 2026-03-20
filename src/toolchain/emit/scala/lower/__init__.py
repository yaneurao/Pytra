"""Scala backend lower stage (EAST3 -> ScalaIR)."""

from __future__ import annotations

from .east3_to_scala_ir import lower_east3_to_scala_ir

__all__ = ["lower_east3_to_scala_ir"]

