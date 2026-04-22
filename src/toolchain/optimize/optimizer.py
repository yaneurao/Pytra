"""EAST3 optimizer framework for toolchain2 (selfhost-safe)."""

from __future__ import annotations

from dataclasses import dataclass

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


class East3OptimizerPass:
    """Base class for optimizer passes."""

    name: str = "Pass"
    min_opt_level: int = 1

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> PassResult:
        _ = east3_doc
        _ = context
        return make_pass_result()


class PassManager:
    """Ordered pass manager."""

    def __init__(self, passes: list[East3OptimizerPass] | None = None) -> None:
        if passes is None:
            self._passes: list[East3OptimizerPass] = []
        else:
            self._passes = passes

    def add_pass(self, pass_obj: East3OptimizerPass) -> None:
        self._passes.append(pass_obj)

    def passes(self) -> list[East3OptimizerPass]:
        out: list[East3OptimizerPass] = []
        for pass_obj in self._passes:
            out.append(pass_obj)
        return out

    def _is_enabled(self, pass_name: str, default_enabled: bool, context: PassContext) -> bool:
        if pass_name in context.disabled_passes:
            return False
        if pass_name in context.enabled_passes:
            return True
        return default_enabled

    def run(self, east3_doc: dict[str, JsonVal], context: PassContext) -> dict[str, JsonVal]:
        _ = east3_doc
        _ = context
        return {
            "changed": False,
            "change_count": 0,
            "warnings": [],
            "elapsed_ms": 0.0,
            "trace": [],
        }


_DEFAULT_NON_ESCAPE_POLICY: dict[str, bool] = {
    "unknown_call_escape": True,
    "unknown_attr_call_escape": True,
    "global_write_escape": True,
    "return_escape_by_default": True,
    "yield_escape_by_default": True,
}


def make_pass_result(
    changed: bool = False,
    change_count: int = 0,
    warnings: list[str] | None = None,
    elapsed_ms: float = 0.0,
) -> PassResult:
    warnings_out: list[str] = []
    if warnings is not None:
        for item in warnings:
            warnings_out.append(item)
    return PassResult(
        changed=changed,
        change_count=change_count,
        warnings=warnings_out,
        elapsed_ms=elapsed_ms,
    )


def merge_pass_result(dst: PassResult, src: PassResult) -> None:
    dst.changed = dst.changed or src.changed
    dst.change_count = dst.change_count + src.change_count
    dst.elapsed_ms = dst.elapsed_ms + src.elapsed_ms
    for w in src.warnings:
        dst.warnings.append(w)



def normalize_non_escape_policy(raw: dict[str, JsonVal] | None) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for key, value in _DEFAULT_NON_ESCAPE_POLICY.items():
        out[key] = value
    if raw is None:
        return out
    for key in _DEFAULT_NON_ESCAPE_POLICY:
        value = raw.get(key)
        if value is True:
            out[key] = True
        elif value is False:
            out[key] = False
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
    debug_flags_out: dict[str, JsonVal] = {}
    if debug_flags is not None:
        for key, value in debug_flags.items():
            debug_flags_out[key] = value
    enabled_out: set[str] = set()
    if enabled_passes is not None:
        for name in enabled_passes:
            enabled_out.add(name)
    disabled_out: set[str] = set()
    if disabled_passes is not None:
        for name in disabled_passes:
            disabled_out.add(name)
    return PassContext(
        opt_level=opt_level,
        target_lang=target_lang,
        debug_flags=debug_flags_out,
        enabled_passes=enabled_out,
        disabled_passes=disabled_out,
        non_escape_policy=normalize_non_escape_policy(non_escape_policy),
    )



def resolve_opt_level(opt_level: str | int) -> int:
    text = str(opt_level).strip()
    if text == "":
        return 1
    if text == "0":
        return 0
    if text == "1":
        return 1
    if text == "2":
        return 2
    raise ValueError("invalid --opt-level: " + text)



def resolve_east3_opt_level(opt_level: str | int) -> int:
    return resolve_opt_level(opt_level)



def resolve_negative_index_mode(mode: str, opt_level: str | int = 1) -> str:
    text = mode.strip()
    if text == "":
        level = resolve_opt_level(opt_level)
        if level == 0:
            return "always"
        if level == 2:
            return "off"
        return "const_only"
    if text == "always" or text == "const_only" or text == "off":
        return text
    raise ValueError("invalid --negative-index-mode: " + text)



def resolve_bounds_check_mode(mode: str, opt_level: str | int = 1) -> str:
    text = mode.strip()
    if text == "":
        level = resolve_opt_level(opt_level)
        if level == 0:
            return "always"
        return "off"
    if text == "always" or text == "debug" or text == "off":
        return text
    raise ValueError("invalid --bounds-check-mode: " + text)



def parse_east3_opt_pass_overrides(spec: str) -> tuple[set[str], set[str]]:
    enabled: set[str] = set()
    disabled: set[str] = set()
    text = spec.strip()
    if text == "":
        return enabled, disabled
    for raw in text.split(","):
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
    return PassManager([])



def optimize_east3_document(
    east3_doc: dict[str, JsonVal],
    opt_level: int = 1,
    target_lang: str = "",
    opt_pass_spec: str = "",
    debug_flags: dict[str, JsonVal] | None = None,
    non_escape_policy: dict[str, JsonVal] | None = None,
    pass_manager: PassManager | None = None,
) -> tuple[dict[str, JsonVal], dict[str, JsonVal]]:
    level = resolve_opt_level(opt_level)
    enabled, disabled = parse_east3_opt_pass_overrides(opt_pass_spec)
    context = make_pass_context(
        opt_level=level,
        target_lang=target_lang,
        debug_flags=debug_flags,
        enabled_passes=enabled,
        disabled_passes=disabled,
        non_escape_policy=non_escape_policy,
    )
    if pass_manager is None:
        manager = build_default_pass_manager()
    else:
        manager = pass_manager
    report = manager.run(east3_doc, context)
    report["opt_level"] = level
    report["target_lang"] = target_lang
    enabled_list: list[str] = []
    for name in enabled:
        enabled_list.append(name)
    disabled_list: list[str] = []
    for name in disabled:
        disabled_list.append(name)
    report["enabled_passes"] = sorted(enabled_list)
    report["disabled_passes"] = sorted(disabled_list)
    policy_out: dict[str, JsonVal] = {}
    for key, value in context.non_escape_policy.items():
        policy_out[key] = value
    report["non_escape_policy"] = policy_out
    return east3_doc, report



def optimize_east3_doc_only(
    east3_doc: dict[str, JsonVal],
    opt_level: int = 1,
    target_lang: str = "",
    opt_pass_spec: str = "",
    debug_flags: dict[str, JsonVal] | None = None,
    non_escape_policy: dict[str, JsonVal] | None = None,
    pass_manager: PassManager | None = None,
) -> dict[str, JsonVal]:
    optimized_doc, _report = optimize_east3_document(
        east3_doc,
        opt_level,
        target_lang,
        opt_pass_spec,
        debug_flags,
        non_escape_policy,
        pass_manager,
    )
    return optimized_doc
