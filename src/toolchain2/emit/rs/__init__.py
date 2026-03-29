"""toolchain2/emit/rs: EAST3 → Rust source emitter.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from toolchain2.emit.rs.emitter import emit_rs_module

__all__ = ["emit_rs_module"]
