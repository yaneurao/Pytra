"""EAST3 optimizer scaffold (`EAST3 -> EAST3`)."""

from __future__ import annotations

import re

from pytra.std import time
from pytra.std.typing import Any


PASS_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


class PassContext:
    """実行時コンテキスト。"""

    def __init__(
        self,
        opt_level: int = 1,
        target_lang: str = "",
        debug_flags: dict[str, object] | None = None,
        enabled_passes: set[str] | None = None,
        disabled_passes: set[str] | None = None,
    ) -> None:
        self.opt_level = opt_level
        self.target_lang = target_lang
        self.debug_flags = dict(debug_flags) if isinstance(debug_flags, dict) else {}
        self.enabled_passes = set(enabled_passes) if isinstance(enabled_passes, set) else set()
        self.disabled_passes = set(disabled_passes) if isinstance(disabled_passes, set) else set()


class PassResult:
    """1 pass 実行結果。"""

    def __init__(
        self,
        *,
        changed: bool = False,
        change_count: int = 0,
        warnings: list[str] | None = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        self.changed = changed
        self.change_count = change_count
        self.warnings = list(warnings) if isinstance(warnings, list) else []
        self.elapsed_ms = elapsed_ms

    def merge(self, other: "PassResult") -> None:
        """集計値へ加算する。"""
        self.changed = self.changed or other.changed
        self.change_count += other.change_count
        self.elapsed_ms += other.elapsed_ms
        for item in other.warnings:
            self.warnings.append(item)

    def to_dict(self) -> dict[str, object]:
        return {
            "changed": self.changed,
            "change_count": self.change_count,
            "warnings": list(self.warnings),
            "elapsed_ms": self.elapsed_ms,
        }


class East3OptimizerPass:
    """各 pass の最小インターフェース。"""

    name = "Pass"
    min_opt_level = 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = east3_doc
        _ = context
        return PassResult()


class PassManager:
    """順序固定 pass manager。"""

    def __init__(self, passes: list[East3OptimizerPass] | None = None) -> None:
        self._passes = list(passes) if isinstance(passes, list) else []

    def add_pass(self, pass_obj: East3OptimizerPass) -> None:
        self._passes.append(pass_obj)

    def passes(self) -> list[East3OptimizerPass]:
        return list(self._passes)

    def _is_enabled(self, pass_name: str, *, default_enabled: bool, context: PassContext) -> bool:
        if pass_name in context.disabled_passes:
            return False
        if pass_name in context.enabled_passes:
            return True
        return default_enabled

    def run(self, east3_doc: dict[str, object], context: PassContext) -> dict[str, object]:
        trace: list[dict[str, object]] = []
        summary = PassResult()
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
            result = pass_obj.run(east3_doc, context)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if not isinstance(result, PassResult):
                raise RuntimeError("optimizer pass must return PassResult: " + pass_name)
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


def resolve_east3_opt_level(opt_level: str | int | object) -> int:
    """`--east3-opt-level` 値を正規化する。"""
    if isinstance(opt_level, int):
        level = opt_level
    elif isinstance(opt_level, str):
        text = opt_level.strip()
        if text == "":
            level = 1
        elif text in {"0", "1", "2"}:
            level = int(text)
        else:
            raise ValueError("invalid --east3-opt-level: " + text)
    else:
        raise ValueError("invalid --east3-opt-level")
    if level < 0 or level > 2:
        raise ValueError("invalid --east3-opt-level: " + str(level))
    return level


def parse_east3_opt_pass_overrides(spec: str) -> tuple[set[str], set[str]]:
    """`--east3-opt-pass` を `(+set, -set)` へ展開する。"""
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
            raise ValueError("invalid --east3-opt-pass token: " + item)
        name = item[1:].strip()
        if name == "" or PASS_NAME_RE.match(name) is None:
            raise ValueError("invalid --east3-opt-pass token: " + item)
        if item[0] == "+":
            enabled.add(name)
            if name in disabled:
                disabled.remove(name)
        else:
            disabled.add(name)
            if name in enabled:
                enabled.remove(name)
    return enabled, disabled


def build_default_pass_manager() -> PassManager:
    """既定 pass 列を読み込んだ manager を構築する。"""
    from pytra.compiler.east_parts.east3_opt_passes import build_default_passes

    return PassManager(build_default_passes())


def optimize_east3_document(
    east3_doc: dict[str, object],
    *,
    opt_level: str | int | object = 1,
    target_lang: str = "",
    opt_pass_spec: str = "",
    debug_flags: dict[str, object] | None = None,
    pass_manager: PassManager | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """`EAST3` に pass manager を適用する。"""
    if not isinstance(east3_doc, dict):
        raise RuntimeError("EAST3 root must be a dict")
    if east3_doc.get("kind") != "Module":
        raise RuntimeError("EAST3 root kind must be Module")
    stage_any = east3_doc.get("east_stage")
    if not isinstance(stage_any, int) or stage_any != 3:
        raise RuntimeError("EAST3 document must have east_stage=3")

    level = resolve_east3_opt_level(opt_level)
    enabled, disabled = parse_east3_opt_pass_overrides(opt_pass_spec)
    context = PassContext(
        opt_level=level,
        target_lang=target_lang,
        debug_flags=debug_flags,
        enabled_passes=enabled,
        disabled_passes=disabled,
    )
    manager = pass_manager if isinstance(pass_manager, PassManager) else build_default_pass_manager()
    report = manager.run(east3_doc, context)
    report["opt_level"] = level
    report["target_lang"] = target_lang
    report["enabled_passes"] = sorted(list(enabled))
    report["disabled_passes"] = sorted(list(disabled))
    return east3_doc, report


def render_east3_opt_trace(report: dict[str, object]) -> str:
    """人間向けトレース文字列へ整形する。"""
    opt_level = report.get("opt_level", 1)
    target_lang = report.get("target_lang", "")
    trace_any = report.get("trace", [])
    trace = trace_any if isinstance(trace_any, list) else []
    lines: list[str] = []
    lines.append("east3_optimizer_trace:")
    lines.append("  opt_level: " + str(opt_level))
    lines.append("  target_lang: " + str(target_lang))
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
    lines.append("  summary:")
    lines.append("    changed: " + ("true" if bool(report.get("changed", False)) else "false"))
    lines.append("    change_count: " + str(int(report.get("change_count", 0))))
    lines.append("    elapsed_ms: " + f"{float(report.get('elapsed_ms', 0.0)):.3f}")
    warnings_any = report.get("warnings", [])
    warnings = warnings_any if isinstance(warnings_any, list) else []
    if len(warnings) == 0:
        lines.append("    warnings: []")
    else:
        lines.append("    warnings:")
        for item in warnings:
            lines.append("      - " + str(item))
    return "\n".join(lines) + "\n"

