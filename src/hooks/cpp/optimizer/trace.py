"""Trace rendering for C++ optimizer runs."""

from __future__ import annotations

from pytra.std.typing import Any


def render_cpp_opt_trace(report: dict[str, Any]) -> str:
    """Render human-readable C++ optimizer trace text."""
    opt_level = report.get("opt_level", 1)
    target_cpp_std = report.get("target_cpp_std", "c++20")
    trace_any = report.get("trace", [])
    trace = trace_any if isinstance(trace_any, list) else []
    lines: list[str] = []
    lines.append("cpp_optimizer_trace:")
    lines.append("  opt_level: " + str(opt_level))
    lines.append("  target_cpp_std: " + str(target_cpp_std))
    lines.append("  passes:")
    if len(trace) == 0:
        lines.append("    - (none)")
    else:
        for item in trace:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            enabled = bool(item.get("enabled", False))
            changed = bool(item.get("changed", False))
            change_count = int(item.get("change_count", 0))
            elapsed_ms = float(item.get("elapsed_ms", 0.0))
            lines.append(
                "    - "
                + name
                + " enabled="
                + ("true" if enabled else "false")
                + " changed="
                + ("true" if changed else "false")
                + " count="
                + str(change_count)
                + " elapsed_ms="
                + f"{elapsed_ms:.3f}"
            )
    return "\n".join(lines) + "\n"

