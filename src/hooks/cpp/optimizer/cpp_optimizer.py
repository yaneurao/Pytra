"""C++ backend optimizer scaffold (`Cpp IR -> Cpp IR`)."""

from __future__ import annotations

import re

from pytra.std import time
from pytra.std.typing import Any

from hooks.cpp.optimizer.context import CppOptContext
from hooks.cpp.optimizer.context import CppOptimizerPass
from hooks.cpp.optimizer.context import CppOptResult


PASS_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


class CppPassManager:
    """Ordered pass manager for C++ optimizer."""

    def __init__(self, passes: list[CppOptimizerPass] | None = None) -> None:
        self._passes = list(passes) if isinstance(passes, list) else []

    def add_pass(self, pass_obj: CppOptimizerPass) -> None:
        self._passes.append(pass_obj)

    def passes(self) -> list[CppOptimizerPass]:
        return list(self._passes)

    def _is_enabled(self, pass_name: str, *, default_enabled: bool, context: CppOptContext) -> bool:
        if pass_name in context.disabled_passes:
            return False
        if pass_name in context.enabled_passes:
            return True
        return default_enabled

    def run(self, cpp_ir: dict[str, Any], context: CppOptContext) -> dict[str, object]:
        trace: list[dict[str, object]] = []
        summary = CppOptResult()
        for pass_obj in self._passes:
            pass_name = str(pass_obj.name)
            default_enabled = context.opt_level >= int(pass_obj.min_opt_level)
            enabled = self._is_enabled(pass_name, default_enabled=default_enabled, context=context)
            if not enabled:
                trace.append(
                    {
                        "name": pass_name,
                        "enabled": False,
                        "changed": False,
                        "change_count": 0,
                        "elapsed_ms": 0.0,
                        "warnings": [],
                    }
                )
                continue
            start = time.perf_counter()
            result = pass_obj.run(cpp_ir, context)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if not isinstance(result, CppOptResult):
                raise RuntimeError("cpp optimizer pass must return CppOptResult: " + pass_name)
            result.elapsed_ms = elapsed_ms
            summary.merge(result)
            trace.append(
                {
                    "name": pass_name,
                    "enabled": True,
                    "changed": result.changed,
                    "change_count": result.change_count,
                    "elapsed_ms": result.elapsed_ms,
                    "warnings": list(result.warnings),
                }
            )
        out = summary.to_dict()
        out["trace"] = trace
        return out


def resolve_cpp_opt_level(opt_level: str | int | object) -> int:
    """Normalize `--cpp-opt-level`-like values."""
    if isinstance(opt_level, int):
        level = opt_level
    elif isinstance(opt_level, str):
        text = opt_level.strip()
        if text == "":
            level = 1
        elif text in {"0", "1", "2"}:
            level = int(text)
        else:
            raise ValueError("invalid --cpp-opt-level: " + text)
    else:
        raise ValueError("invalid --cpp-opt-level")
    if level < 0 or level > 2:
        raise ValueError("invalid --cpp-opt-level: " + str(level))
    return level


def parse_cpp_opt_pass_overrides(spec: str) -> tuple[set[str], set[str]]:
    """Parse pass override text to `(enabled, disabled)` sets."""
    enabled: set[str] = set()
    disabled: set[str] = set()
    text = spec.strip()
    if text == "":
        return enabled, disabled
    raw_items = text.split(",")
    for raw in raw_items:
        item = raw.strip()
        if item == "":
            continue
        if len(item) < 2 or (item[0] != "+" and item[0] != "-"):
            raise ValueError("invalid --cpp-opt-pass token: " + item)
        name = item[1:].strip()
        if name == "" or PASS_NAME_RE.match(name) is None:
            raise ValueError("invalid --cpp-opt-pass token: " + item)
        if item[0] == "+":
            enabled.add(name)
            if name in disabled:
                disabled.remove(name)
        else:
            disabled.add(name)
            if name in enabled:
                enabled.remove(name)
    return enabled, disabled


def build_default_cpp_pass_manager() -> CppPassManager:
    from hooks.cpp.optimizer.passes import build_default_cpp_passes

    return CppPassManager(build_default_cpp_passes())


def optimize_cpp_ir(
    cpp_ir: dict[str, Any],
    *,
    opt_level: str | int | object = 1,
    target_cpp_std: str = "c++20",
    opt_pass_spec: str = "",
    debug_flags: dict[str, object] | None = None,
    pass_manager: CppPassManager | None = None,
) -> tuple[dict[str, Any], dict[str, object]]:
    """Apply C++ optimizer pass manager."""
    if not isinstance(cpp_ir, dict):
        raise RuntimeError("C++ IR root must be a dict")
    level = resolve_cpp_opt_level(opt_level)
    enabled, disabled = parse_cpp_opt_pass_overrides(opt_pass_spec)
    context = CppOptContext(
        opt_level=level,
        target_cpp_std=target_cpp_std,
        debug_flags=debug_flags,
        enabled_passes=enabled,
        disabled_passes=disabled,
    )
    manager = pass_manager if isinstance(pass_manager, CppPassManager) else build_default_cpp_pass_manager()
    report = manager.run(cpp_ir, context)
    report["opt_level"] = level
    report["target_cpp_std"] = target_cpp_std
    report["enabled_passes"] = sorted(list(enabled))
    report["disabled_passes"] = sorted(list(disabled))
    return cpp_ir, report

