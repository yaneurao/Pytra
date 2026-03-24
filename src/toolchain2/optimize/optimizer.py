"""EAST3 optimizer framework for toolchain2 (selfhost-safe)."""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std import time
from pytra.std.json import JsonVal


@dataclass
class PassContext:
    """Runtime context for optimizer passes."""

    opt_level: int
    target_lang: str
    debug_flags: dict[str, JsonVal]
    enabled_passes: set[str]
    disabled_passes: set[str]
    non_escape_policy: dict[str, bool]


@dataclass
class PassResult:
    """Result of a single pass execution."""

    changed: bool
    change_count: int
    warnings: list[str]
    elapsed_ms: float


def make_pass_result(
    *,
    changed: bool = False,
    change_count: int = 0,
    warnings: list[str] | None = None,
    elapsed_ms: float = 0.0,
) -> PassResult:
    """Create a PassResult with defaults."""
    return PassResult(
        changed=changed,
        change_count=change_count,
        warnings=list(warnings) if isinstance(warnings, list) else [],
        elapsed_ms=elapsed_ms,
    )


def merge_pass_result(dst: PassResult, src: PassResult) -> None:
    """Merge src into dst."""
    dst.changed = dst.changed or src.changed
    dst.change_count = dst.change_count + src.change_count
    dst.elapsed_ms = dst.elapsed_ms + src.elapsed_ms
    for w in src.warnings:
        dst.warnings.append(w)


_DEFAULT_NON_ESCAPE_POLICY: dict[str, bool] = {
    "unknown_call_escape": True,
    "unknown_attr_call_escape": True,
    "global_write_escape": True,
    "return_escape_by_default": True,
    "yield_escape_by_default": True,
}


def normalize_non_escape_policy(raw: dict[str, JsonVal] | None) -> dict[str, bool]:
    """Normalize non-escape policy with defaults."""
    out: dict[str, bool] = dict(_DEFAULT_NON_ESCAPE_POLICY)
    if not isinstance(raw, dict):
        return out
    for key in _DEFAULT_NON_ESCAPE_POLICY:
        value = raw.get(key)
        if isinstance(value, bool):
            out[key] = value
    return out


def make_pass_context(
    *,
    opt_level: int = 1,
    target_lang: str = "",
    debug_flags: dict[str, JsonVal] | None = None,
    enabled_passes: set[str] | None = None,
    disabled_passes: set[str] | None = None,
    non_escape_policy: dict[str, JsonVal] | None = None,
) -> PassContext:
    """Create a PassContext with defaults."""
    return PassContext(
        opt_level=opt_level,
        target_lang=target_lang,
        debug_flags=dict(debug_flags) if isinstance(debug_flags, dict) else {},
        enabled_passes=set(enabled_passes) if isinstance(enabled_passes, set) else set(),
        disabled_passes=set(disabled_passes) if isinstance(disabled_passes, set) else set(),
        non_escape_policy=normalize_non_escape_policy(non_escape_policy),
    )


class East3OptimizerPass:
    """Base class for optimizer passes."""

    name: str = "Pass"
    min_opt_level: int = 1

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        """Run the pass on the document. Override in subclasses."""
        _ = east3_doc
        _ = context
        return make_pass_result()


class PassManager:
    """Ordered pass manager."""

    def __init__(self, passes: list[East3OptimizerPass] | None = None) -> None:
        self._passes: list[East3OptimizerPass] = list(passes) if isinstance(passes, list) else []

    def add_pass(self, pass_obj: East3OptimizerPass) -> None:
        self._passes.append(pass_obj)

    def passes(self) -> list[East3OptimizerPass]:
        return list(self._passes)

    def _is_enabled(self, pass_name: str, default_enabled: bool, context: PassContext) -> bool:
        if pass_name in context.disabled_passes:
            return False
        if pass_name in context.enabled_passes:
            return True
        return default_enabled

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> dict[str, JsonVal]:
        trace: list[JsonVal] = []
        summary = make_pass_result()
        for pass_obj in self._passes:
            pass_name = str(pass_obj.name)
            default_enabled = context.opt_level >= int(pass_obj.min_opt_level)
            enabled = self._is_enabled(pass_name, default_enabled, context)
            if not enabled:
                trace.append({
                    "name": pass_name,
                    "enabled": False,
                    "changed": False,
                    "change_count": 0,
                    "elapsed_ms": 0.0,
                    "warnings": [],
                })
                continue
            start = time.perf_counter()
            result = pass_obj.run(east3_doc, context)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            result.elapsed_ms = elapsed_ms
            merge_pass_result(summary, result)
            trace.append({
                "name": pass_name,
                "enabled": True,
                "changed": result.changed,
                "change_count": result.change_count,
                "elapsed_ms": result.elapsed_ms,
                "warnings": list(result.warnings),
            })
        out: dict[str, JsonVal] = {
            "changed": summary.changed,
            "change_count": summary.change_count,
            "warnings": list(summary.warnings),
            "elapsed_ms": summary.elapsed_ms,
            "trace": trace,
        }
        return out


def resolve_east3_opt_level(opt_level: str | int) -> int:
    """Normalize --east3-opt-level value."""
    if isinstance(opt_level, int):
        level = opt_level
    elif isinstance(opt_level, str):
        text = opt_level.strip()
        if text == "":
            level = 1
        elif text == "0" or text == "1" or text == "2":
            level = int(text)
        else:
            raise ValueError("invalid --east3-opt-level: " + text)
    else:
        raise ValueError("invalid --east3-opt-level")
    if level < 0 or level > 2:
        raise ValueError("invalid --east3-opt-level: " + str(level))
    return level


def parse_east3_opt_pass_overrides(spec: str) -> tuple[set[str], set[str]]:
    """Parse --east3-opt-pass into (enabled, disabled) sets."""
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
        if name == "":
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
    """Build default pass manager with all local passes."""
    from toolchain2.optimize.passes import build_local_only_passes

    return PassManager(build_local_only_passes())


def optimize_east3_document(
    east3_doc: dict[str, JsonVal],
    *,
    opt_level: int = 1,
    target_lang: str = "",
    opt_pass_spec: str = "",
    debug_flags: dict[str, JsonVal] | None = None,
    non_escape_policy: dict[str, JsonVal] | None = None,
    pass_manager: PassManager | None = None,
) -> tuple[dict[str, JsonVal], dict[str, JsonVal]]:
    """Apply pass manager to an EAST3 document."""
    if not isinstance(east3_doc, dict):
        raise RuntimeError("EAST3 root must be a dict")
    if east3_doc.get("kind") != "Module":
        raise RuntimeError("EAST3 root kind must be Module")
    stage_val = east3_doc.get("east_stage")
    if not isinstance(stage_val, int) or stage_val != 3:
        raise RuntimeError("EAST3 document must have east_stage=3")

    level = resolve_east3_opt_level(opt_level)
    enabled, disabled = parse_east3_opt_pass_overrides(opt_pass_spec)
    context = make_pass_context(
        opt_level=level,
        target_lang=target_lang,
        debug_flags=debug_flags,
        enabled_passes=enabled,
        disabled_passes=disabled,
        non_escape_policy=non_escape_policy,
    )
    manager = pass_manager if isinstance(pass_manager, PassManager) else build_default_pass_manager()
    report = manager.run(east3_doc, context)
    report["opt_level"] = level
    report["target_lang"] = target_lang
    report["enabled_passes"] = sorted(list(enabled))
    report["disabled_passes"] = sorted(list(disabled))
    report["non_escape_policy"] = dict(context.non_escape_policy)
    return east3_doc, report
