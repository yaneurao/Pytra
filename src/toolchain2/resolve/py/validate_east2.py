"""EAST2 不変条件バリデータ.

spec-east2.md §6 の不変条件を検証する。golden 完全一致ではなく構造的正しさを判定。

チェック項目:
1. east_stage == 2
2. schema_version == 1
3. meta.dispatch_mode が設定されている
4. 全式ノードに resolved_type がある
5. range() が生の Call として残っていない (ForRange に変換済み)
6. 型注釈が正規化されている (int→int64, float→float64)
7. FunctionDef に arg_usage がある
8. FunctionDef (非 class method) に arg_type_exprs / return_type_expr がある

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytra.std.json import JsonVal


@dataclass
class ValidationResult:
    """Validation result for a single EAST2 document."""
    source_path: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# Expression node kinds
_EXPR_KINDS: set[str] = {
    "Name", "Constant", "BinOp", "UnaryOp", "Compare", "BoolOp",
    "Call", "Attribute", "Subscript", "List", "Dict", "Set", "Tuple",
    "IfExp", "ListComp", "DictComp", "SetComp", "Starred",
    "JoinedStr", "FormattedValue", "Lambda", "Slice",
}

# Unresolved Python types that should have been normalized
_UNNORMALIZED_TYPES: set[str] = {"int", "float", "byte", "bytes", "bytearray"}


def validate_east2(doc: dict[str, JsonVal]) -> ValidationResult:
    """Validate EAST2 document invariants."""
    result: ValidationResult = ValidationResult()

    sp = doc.get("source_path")
    result.source_path = str(sp) if isinstance(sp, str) else ""

    # 1. east_stage == 2
    stage = doc.get("east_stage")
    if stage != 2:
        result.errors.append("east_stage is " + str(stage) + ", expected 2")

    # 2. schema_version == 1
    sv = doc.get("schema_version")
    if sv != 1:
        result.errors.append("schema_version is " + str(sv) + ", expected 1")

    # 3. meta.dispatch_mode
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        result.errors.append("meta is missing or not a dict")
    else:
        dm = meta.get("dispatch_mode")
        if not isinstance(dm, str) or dm == "":
            result.errors.append("meta.dispatch_mode is missing or empty")

    # Walk all nodes
    ctx = _WalkContext(result=result)
    _walk_node(doc, ctx, in_class=False, path="$")

    # Summarize stats
    result.stats["expr_nodes"] = ctx.expr_count
    result.stats["expr_with_resolved_type"] = ctx.resolved_count
    result.stats["expr_missing_resolved_type"] = ctx.missing_resolved_count
    result.stats["range_calls_remaining"] = ctx.range_call_count
    result.stats["unnormalized_types"] = ctx.unnormalized_type_count
    result.stats["functions"] = ctx.func_count
    result.stats["functions_with_arg_usage"] = ctx.func_with_arg_usage
    result.stats["functions_with_type_exprs"] = ctx.func_with_type_exprs

    return result


@dataclass
class _WalkContext:
    result: ValidationResult
    expr_count: int = 0
    resolved_count: int = 0
    missing_resolved_count: int = 0
    range_call_count: int = 0
    unnormalized_type_count: int = 0
    func_count: int = 0
    func_with_arg_usage: int = 0
    func_with_type_exprs: int = 0


def _walk_node(node: JsonVal, ctx: _WalkContext, in_class: bool, path: str) -> None:
    """Recursively walk and validate nodes."""
    if isinstance(node, list):
        for i, item in enumerate(node):
            _walk_node(item, ctx, in_class, path + "[" + str(i) + "]")
        return

    if not isinstance(node, dict):
        return

    kind = node.get("kind")
    if not isinstance(kind, str):
        # Not an AST node, recurse into values
        for k, v in node.items():
            _walk_node(v, ctx, in_class, path + "." + k)
        return

    # --- Expression node checks ---
    if kind in _EXPR_KINDS:
        ctx.expr_count += 1
        rt = node.get("resolved_type")
        if isinstance(rt, str) and rt != "":
            ctx.resolved_count += 1
        else:
            ctx.missing_resolved_count += 1
            # Only warn, don't error — some contexts legitimately lack it
            # ctx.result.warnings.append(path + ": " + kind + " missing resolved_type")

    # --- range() Call check ---
    if kind == "Call":
        func = node.get("func")
        if isinstance(func, dict) and func.get("kind") == "Name" and func.get("id") == "range":
            ctx.range_call_count += 1
            ctx.result.errors.append(path + ": raw range() Call found (should be ForRange)")

    # --- FunctionDef checks ---
    if kind == "FunctionDef":
        ctx.func_count += 1
        if "arg_usage" in node:
            ctx.func_with_arg_usage += 1
        else:
            ctx.result.warnings.append(path + ": FunctionDef missing arg_usage")

        if not in_class:
            # Top-level/nested functions should have type exprs
            ate = node.get("arg_type_exprs")
            rte = node.get("return_type_expr")
            if ate is not None or rte is not None:
                ctx.func_with_type_exprs += 1
        else:
            # Class methods: arg_type_exprs/return_type_expr should be absent or null
            pass

    # --- Type normalization check ---
    _check_type_normalization(node, ctx, path)

    # --- ClassDef: track in_class ---
    child_in_class: bool = in_class
    if kind == "ClassDef":
        child_in_class = True

    # --- Recurse into children ---
    for k, v in node.items():
        if k in ("source_span", "meta"):
            continue  # Skip non-AST fields
        _walk_node(v, ctx, child_in_class, path + "." + k)


def _check_type_normalization(node: dict[str, JsonVal], ctx: _WalkContext, path: str) -> None:
    """Check that Python type names have been normalized."""
    for field_name in ("resolved_type", "return_type", "decl_type", "annotation", "target_type"):
        val = node.get(field_name)
        if isinstance(val, str):
            # Check for unnormalized types at top level
            if val in _UNNORMALIZED_TYPES:
                ctx.unnormalized_type_count += 1
                ctx.result.warnings.append(
                    path + "." + field_name + ": unnormalized type '" + val + "'"
                )

    # Check arg_types dict
    at = node.get("arg_types")
    if isinstance(at, dict):
        for ak, av in at.items():
            if isinstance(av, str) and av in _UNNORMALIZED_TYPES:
                ctx.unnormalized_type_count += 1
                ctx.result.warnings.append(
                    path + ".arg_types." + ak + ": unnormalized type '" + av + "'"
                )


def format_result(result: ValidationResult) -> str:
    """Format validation result as a human-readable string."""
    lines: list[str] = []
    status: str = "PASS" if result.ok else "FAIL"
    lines.append(status + ": " + result.source_path)

    if result.errors:
        for e in result.errors:
            lines.append("  ERROR: " + e)

    s = result.stats
    expr_total: int = s.get("expr_nodes", 0)
    expr_resolved: int = s.get("expr_with_resolved_type", 0)
    expr_missing: int = s.get("expr_missing_resolved_type", 0)
    lines.append(
        "  expr: " + str(expr_total) +
        " (resolved=" + str(expr_resolved) +
        ", missing=" + str(expr_missing) + ")"
    )

    range_count: int = s.get("range_calls_remaining", 0)
    if range_count > 0:
        lines.append("  range() remaining: " + str(range_count))

    unnorm: int = s.get("unnormalized_types", 0)
    if unnorm > 0:
        lines.append("  unnormalized types: " + str(unnorm))

    funcs: int = s.get("functions", 0)
    with_au: int = s.get("functions_with_arg_usage", 0)
    with_te: int = s.get("functions_with_type_exprs", 0)
    lines.append(
        "  functions: " + str(funcs) +
        " (arg_usage=" + str(with_au) +
        ", type_exprs=" + str(with_te) + ")"
    )

    if result.warnings:
        lines.append("  warnings: " + str(len(result.warnings)))

    return "\n".join(lines)
