"""Detect `Any` type annotations in transpile-target Python and raise a compile error.

This pass is NOT included in ``build_local_only_passes()`` by default.
It is intended to be enabled explicitly (e.g. via ``--east3-opt-pass
+AnyAnnotationProhibitionPass``) until the stdlib has been migrated away
from ``Any`` (see P5-ANY-ELIM-OBJECT-FREE-01-S2-02).
"""

from __future__ import annotations

from typing import Any

from toolchain.compile.east3_optimizer import East3OptimizerPass
from toolchain.compile.east3_optimizer import PassContext
from toolchain.compile.east3_optimizer import PassResult


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _annotation_contains_any(type_str: str) -> bool:
    """Return True if *type_str* contains ``Any`` as a standalone type token.

    Examples::

        _annotation_contains_any("Any")             # True
        _annotation_contains_any("list[Any]")       # True
        _annotation_contains_any("dict[str, Any]")  # True
        _annotation_contains_any("AnyFoo")          # False
        _annotation_contains_any("int")             # False
    """
    if not type_str:
        return False
    cur = ""
    for ch in type_str:
        if ch in "[], |":
            if cur == "Any":
                return True
            cur = ""
        else:
            cur += ch
    return cur == "Any"


class _Violation:
    def __init__(self, *, lineno: int, col: int, context: str, ann: str) -> None:
        self.lineno = lineno
        self.col = col
        self.context = context
        self.ann = ann

    def message(self) -> str:
        loc = f"line {self.lineno}, col {self.col}" if self.lineno > 0 else "unknown location"
        return f"  [{loc}] {self.context}: annotation `{self.ann}` contains `Any`"


def _span(node: dict[str, Any]) -> tuple[int, int]:
    span = node.get("source_span")
    if isinstance(span, dict):
        return int(span.get("lineno", 0)), int(span.get("col", 0))
    return 0, 0


class AnyAnnotationProhibitionPass(East3OptimizerPass):
    """Raise a compile error when ``Any`` appears in a type annotation.

    Checks:

    - ``FunctionDef`` / ``AsyncFunctionDef``: each parameter annotation via
      ``arg_types`` and the return type via ``return_type``.
    - ``AnnAssign``: the ``annotation`` field.

    ``from typing import Any`` imports are not checked (they are allowed as
    annotation-only no-ops).
    """

    name = "AnyAnnotationProhibitionPass"
    min_opt_level = 1

    def _check(
        self,
        type_str: str,
        *,
        lineno: int,
        col: int,
        context: str,
        violations: list[_Violation],
    ) -> None:
        t = _normalize_type_name(type_str)
        if _annotation_contains_any(t):
            violations.append(_Violation(lineno=lineno, col=col, context=context, ann=t))

    def _walk_stmts(
        self,
        stmts: list[Any],
        violations: list[_Violation],
    ) -> None:
        for raw_stmt in stmts:
            if not isinstance(raw_stmt, dict):
                continue
            stmt: dict[str, Any] = raw_stmt
            kind = str(stmt.get("kind", ""))
            lineno, col = _span(stmt)

            if kind == "AnnAssign":
                target_raw = stmt.get("target")
                var_name = ""
                if isinstance(target_raw, dict):
                    var_name = str(target_raw.get("id", target_raw.get("repr", "")))
                ann = _normalize_type_name(stmt.get("annotation"))
                self._check(
                    ann,
                    lineno=lineno,
                    col=col,
                    context=f"variable `{var_name}`",
                    violations=violations,
                )

            elif kind in ("FunctionDef", "AsyncFunctionDef"):
                fn_name = str(stmt.get("name", "?"))

                # Return type
                ret_type = _normalize_type_name(stmt.get("return_type"))
                self._check(
                    ret_type,
                    lineno=lineno,
                    col=col,
                    context=f"return type of `{fn_name}`",
                    violations=violations,
                )

                # Parameter types
                arg_types_raw = stmt.get("arg_types")
                if isinstance(arg_types_raw, dict):
                    for arg_name, arg_type_raw in arg_types_raw.items():
                        arg_type = _normalize_type_name(arg_type_raw)
                        self._check(
                            arg_type,
                            lineno=lineno,
                            col=col,
                            context=f"parameter `{arg_name}` of `{fn_name}`",
                            violations=violations,
                        )

                # Recurse into body
                body_raw = stmt.get("body")
                if isinstance(body_raw, list):
                    self._walk_stmts(body_raw, violations)

            elif kind == "ClassDef":
                body_raw = stmt.get("body")
                if isinstance(body_raw, list):
                    self._walk_stmts(body_raw, violations)

            elif kind in ("If", "While", "For", "With", "Try"):
                for key in ("body", "orelse", "handlers", "finalbody"):
                    sub = stmt.get(key)
                    if isinstance(sub, list):
                        self._walk_stmts(sub, violations)

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        body_raw = east3_doc.get("body")
        if not isinstance(body_raw, list):
            return PassResult()

        violations: list[_Violation] = []
        self._walk_stmts(body_raw, violations)

        if not violations:
            return PassResult()

        lines: list[str] = [
            "AnyAnnotationProhibitionPass: `Any` type annotations are prohibited.",
            "Use a concrete type (e.g. `str`, `int`, `list[str]`), a union type",
            "(e.g. `str | int`), or a user-defined class instead of `Any`.",
            "Violations:",
        ]
        for v in violations:
            lines.append(v.message())
        raise RuntimeError("\n".join(lines))
