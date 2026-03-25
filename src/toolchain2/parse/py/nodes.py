"""EAST1 ノード定義: dataclass ベース (spec-east1.md 準拠)。

§5.1: Any/object 禁止、全フィールド具象型。
§5.2: Python 標準モジュール直接 import 禁止 (typing, dataclasses は例外)。

EAST1 は構文解析の出力。型解決は含まない。
- resolved_type: 出力しない
- type_expr: 出力しない
- borrow_kind: 常に "value"
- casts: 常に []
- semantic_tag / runtime_* / lowered_kind: 出力しない
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from pytra.std.json import JsonVal

from toolchain2.common import kinds as K
from toolchain2.parse.py.source_span import SourceSpan, NULL_SPAN


# ---------------------------------------------------------------------------
# Type expression nodes (型注釈用 — ソースのまま保持)
# ---------------------------------------------------------------------------

@dataclass
class NamedType:
    name: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "NamedType", "name": self.name}

@dataclass
class GenericType:
    base: str
    args: list[Union[NamedType, GenericType]]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "GenericType", "base": self.base, "args": [a.to_jv() for a in self.args]}

TypeExpr = Union[NamedType, GenericType]


# ---------------------------------------------------------------------------
# Trivia nodes
# ---------------------------------------------------------------------------

@dataclass
class TriviaBlank:
    count: int
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "blank", "count": self.count}

@dataclass
class TriviaComment:
    text: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "comment", "text": self.text}

TriviaNode = Union[TriviaBlank, TriviaComment]


# ---------------------------------------------------------------------------
# Import alias
# ---------------------------------------------------------------------------

@dataclass
class ImportAlias:
    name: str
    asname: Optional[str]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"name": self.name, "asname": self.asname}


# ---------------------------------------------------------------------------
# Semantic sub-structures
# ---------------------------------------------------------------------------

@dataclass
class Keyword:
    arg: str
    value_node: Expr  # forward ref
    def to_jv(self) -> dict[str, JsonVal]:
        return {"arg": self.arg, "value": expr_to_jv(self.value_node)}

@dataclass
class Comprehension:
    target: Expr
    iter_expr: Expr
    ifs: list[Expr]
    is_async: bool
    def to_jv(self) -> dict[str, JsonVal]:
        return {"target": expr_to_jv(self.target), "iter": expr_to_jv(self.iter_expr),
                "ifs": [expr_to_jv(e) for e in self.ifs], "is_async": self.is_async}

@dataclass
class DictEntry:
    key: Expr
    value: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        return {"key": expr_to_jv(self.key), "value": expr_to_jv(self.value)}


# ---------------------------------------------------------------------------
# Expression base (EAST1: no resolved_type, borrow_kind="value", casts=[])
# ---------------------------------------------------------------------------

@dataclass
class ExprBase:
    source_span: SourceSpan
    repr_text: str  # JSON key: "repr"

def _expr_base_jv(e: ExprBase) -> dict[str, JsonVal]:
    return {
        "source_span": e.source_span.to_jv(),
        "casts": [],
        "borrow_kind": "value",
        "repr": e.repr_text,
    }


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class Name:
    base: ExprBase
    id: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.NAME}
        d.update(_expr_base_jv(self.base))
        d["id"] = self.id
        return d

@dataclass
class Constant:
    base: ExprBase
    value: Union[int, float, str, bool]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.CONSTANT}
        d.update(_expr_base_jv(self.base))
        d["value"] = self.value
        return d

@dataclass
class BinOp:
    base: ExprBase
    left: Expr
    op: str
    right: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.BIN_OP}
        d.update(_expr_base_jv(self.base))
        d["left"] = expr_to_jv(self.left)
        d["op"] = self.op
        d["right"] = expr_to_jv(self.right)
        return d

@dataclass
class UnaryOp:
    base: ExprBase
    op: str
    operand: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.UNARY_OP}
        d.update(_expr_base_jv(self.base))
        d["op"] = self.op
        d["operand"] = expr_to_jv(self.operand)
        return d

@dataclass
class BoolOp:
    base: ExprBase
    op: str
    values: list[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "BoolOp"}
        d.update(_expr_base_jv(self.base))
        d["op"] = self.op
        d["values"] = [expr_to_jv(v) for v in self.values]
        return d

@dataclass
class Compare:
    base: ExprBase
    left: Expr
    ops: list[str]
    comparators: list[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.COMPARE}
        d.update(_expr_base_jv(self.base))
        d["left"] = expr_to_jv(self.left)
        d["ops"] = list(self.ops)
        d["comparators"] = [expr_to_jv(c) for c in self.comparators]
        return d

@dataclass
class Call:
    base: ExprBase
    func: Expr
    args: list[Expr]
    keywords: list[Keyword]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.CALL}
        d.update(_expr_base_jv(self.base))
        d["func"] = expr_to_jv(self.func)
        d["args"] = [expr_to_jv(a) for a in self.args]
        d["keywords"] = [kw.to_jv() for kw in self.keywords]
        return d

@dataclass
class Attribute:
    base: ExprBase
    value: Expr
    attr: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.ATTRIBUTE}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        d["attr"] = self.attr
        return d

@dataclass
class Subscript:
    base: ExprBase
    value: Expr
    slice_expr: Expr
    is_slice: bool = False
    lowered_kind: Optional[str] = None
    lower: Optional[Expr] = None
    upper: Optional[Expr] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.SUBSCRIPT}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        d["slice"] = expr_to_jv(self.slice_expr)
        if self.lowered_kind is not None:
            d["lowered_kind"] = self.lowered_kind
        if self.is_slice:
            d["lower"] = expr_to_jv(self.lower) if self.lower is not None else None
            d["upper"] = expr_to_jv(self.upper) if self.upper is not None else None
        return d

@dataclass
class SliceExpr:
    lower: Optional[Expr]
    upper: Optional[Expr]
    step: Optional[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Slice",
                "lower": expr_to_jv(self.lower) if self.lower is not None else None,
                "upper": expr_to_jv(self.upper) if self.upper is not None else None,
                "step": expr_to_jv(self.step) if self.step is not None else None}

@dataclass
class IfExp:
    base: ExprBase
    test: Expr
    body: Expr
    orelse: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.IF_EXP}
        d.update(_expr_base_jv(self.base))
        d["test"] = expr_to_jv(self.test)
        d["body"] = expr_to_jv(self.body)
        d["orelse"] = expr_to_jv(self.orelse)
        return d

@dataclass
class ListExpr:
    base: ExprBase
    elements: list[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.LIST}
        d.update(_expr_base_jv(self.base))
        d["elements"] = [expr_to_jv(e) for e in self.elements]
        return d

@dataclass
class TupleExpr:
    base: ExprBase
    elements: list[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.TUPLE}
        d.update(_expr_base_jv(self.base))
        d["elements"] = [expr_to_jv(e) for e in self.elements]
        return d

@dataclass
class SetExpr:
    base: ExprBase
    elements: list[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.SET}
        d.update(_expr_base_jv(self.base))
        d["elements"] = [expr_to_jv(e) for e in self.elements]
        return d

@dataclass
class DictExpr:
    base: ExprBase
    keys: list[Expr]
    dict_values: list[Expr]
    entries: Optional[list[DictEntry]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.DICT}
        d.update(_expr_base_jv(self.base))
        if self.entries is not None:
            d["entries"] = [e.to_jv() for e in self.entries]
        else:
            d["keys"] = [expr_to_jv(k) for k in self.keys]
            d["values"] = [expr_to_jv(v) for v in self.dict_values]
        return d

@dataclass
class ListComp:
    base: ExprBase
    elt: Expr
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.LIST_COMP}
        d.update(_expr_base_jv(self.base))
        d["elt"] = expr_to_jv(self.elt)
        d["generators"] = [g.to_jv() for g in self.generators]
        return d

@dataclass
class FStringText:
    """f-string 内のリテラルテキスト部分 (borrow_kind/casts なし)。"""
    source_span: SourceSpan
    repr_text: str
    value: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.CONSTANT, "source_span": self.source_span.to_jv(),
                "repr": self.repr_text, "value": self.value}

@dataclass
class FormattedValue:
    value: Expr
    format_spec: Optional[str] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "FormattedValue", "value": expr_to_jv(self.value)}
        if self.format_spec is not None:
            d["format_spec"] = self.format_spec
        return d

@dataclass
class JoinedStr:
    base: ExprBase
    values: list[Union[FStringText, FormattedValue]]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "JoinedStr"}
        d.update(_expr_base_jv(self.base))
        d["values"] = [v.to_jv() for v in self.values]
        return d

@dataclass
class LambdaArg:
    name: str
    default_expr: Optional[Expr] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "arg", "arg": self.name, "annotation": None}
        if self.default_expr is not None:
            d["default"] = expr_to_jv(self.default_expr)
        return d

@dataclass
class LambdaExpr:
    base: ExprBase
    args: list[LambdaArg]
    body: Expr
    return_type: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Lambda"}
        d.update(_expr_base_jv(self.base))
        d["args"] = [a.to_jv() for a in self.args]
        d["body"] = expr_to_jv(self.body)
        d["return_type"] = self.return_type
        return d

@dataclass
class RangeExpr:
    base: ExprBase
    start: Expr
    stop: Expr
    step: Expr
    range_mode: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "RangeExpr"}
        d.update(_expr_base_jv(self.base))
        d["start"] = expr_to_jv(self.start)
        d["stop"] = expr_to_jv(self.stop)
        d["step"] = expr_to_jv(self.step)
        d["range_mode"] = self.range_mode
        return d


@dataclass
class SetComp:
    base: ExprBase
    elt: Expr
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "SetComp"}
        d.update(_expr_base_jv(self.base))
        d["elt"] = expr_to_jv(self.elt)
        d["generators"] = [g.to_jv() for g in self.generators]
        return d

@dataclass
class DictComp:
    base: ExprBase
    key: Expr
    value: Expr
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "DictComp"}
        d.update(_expr_base_jv(self.base))
        d["key"] = expr_to_jv(self.key)
        d["value"] = expr_to_jv(self.value)
        d["generators"] = [g.to_jv() for g in self.generators]
        return d

@dataclass
class Starred:
    base: ExprBase
    value: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.STARRED}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        return d

Expr = Union[
    Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute,
    Subscript, SliceExpr, IfExp, ListExpr, SetExpr, TupleExpr, DictExpr,
    ListComp, SetComp, DictComp, JoinedStr,
    RangeExpr, LambdaExpr, Starred,
]

def expr_to_jv(e: Expr) -> dict[str, JsonVal]:
    return e.to_jv()


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class Import:
    source_span: SourceSpan
    names: list[ImportAlias]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Import", "source_span": self.source_span.to_jv(),
                "names": [n.to_jv() for n in self.names]}

@dataclass
class ImportFrom:
    source_span: SourceSpan
    module: str
    names: list[ImportAlias]
    level: int
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "ImportFrom", "source_span": self.source_span.to_jv(),
                "module": self.module, "names": [n.to_jv() for n in self.names], "level": self.level}

@dataclass
class AnnAssign:
    source_span: SourceSpan
    target: Expr
    annotation: str
    value: Optional[Expr]
    declare: bool
    node_meta: Optional[dict[str, JsonVal]] = None
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": K.ANN_ASSIGN, "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target), "annotation": self.annotation,
            "value": expr_to_jv(self.value) if self.value is not None else None,
            "declare": self.declare,
        }
        if self.node_meta is not None:
            d["meta"] = dict(self.node_meta)
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d

@dataclass
class Assign:
    source_span: SourceSpan
    target: Expr
    value: Expr
    declare: bool
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": K.ASSIGN, "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target), "value": expr_to_jv(self.value),
            "declare": self.declare,
        }
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d

@dataclass
class AugAssign:
    source_span: SourceSpan
    target: Expr
    op: str
    value: Expr
    declare: bool
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.AUG_ASSIGN, "source_span": self.source_span.to_jv(),
                "target": expr_to_jv(self.target), "op": self.op,
                "value": expr_to_jv(self.value), "declare": self.declare}

@dataclass
class ExprStmt:
    source_span: SourceSpan
    value: Expr
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.EXPR, "source_span": self.source_span.to_jv(),
                                  "value": expr_to_jv(self.value)}
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d

@dataclass
class Swap:
    source_span: SourceSpan
    left: Expr
    right: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.SWAP, "source_span": self.source_span.to_jv(),
                "left": expr_to_jv(self.left), "right": expr_to_jv(self.right)}

@dataclass
class Return:
    source_span: SourceSpan
    value: Expr
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.RETURN, "source_span": self.source_span.to_jv(),
                                  "value": expr_to_jv(self.value)}
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d

@dataclass
class Yield:
    source_span: SourceSpan
    value: Expr
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.YIELD, "source_span": self.source_span.to_jv(),
                "value": expr_to_jv(self.value)}

@dataclass
class Raise:
    source_span: SourceSpan
    exc: Expr
    cause: Optional[Expr]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Raise", "source_span": self.source_span.to_jv(),
                "exc": expr_to_jv(self.exc),
                "cause": expr_to_jv(self.cause) if self.cause is not None else None}

@dataclass
class ExceptHandler:
    exc_type_expr: Optional[Expr]
    name: Optional[str]
    body: list[Stmt]
    source_span: SourceSpan
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "ExceptHandler",
                "type": expr_to_jv(self.exc_type_expr) if self.exc_type_expr is not None else None,
                "name": self.name,
                "body": [stmt_to_jv(s) for s in self.body]}

@dataclass
class Try:
    source_span: SourceSpan
    body: list[Stmt]
    handlers: list[ExceptHandler]
    orelse: list[Stmt]
    finalbody: list[Stmt]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.TRY, "source_span": self.source_span.to_jv(),
                "body": [stmt_to_jv(s) for s in self.body],
                "handlers": [h.to_jv() for h in self.handlers],
                "orelse": [stmt_to_jv(s) for s in self.orelse],
                "finalbody": [stmt_to_jv(s) for s in self.finalbody]}

@dataclass
class Pass:
    source_span: SourceSpan
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Pass", "source_span": self.source_span.to_jv()}

@dataclass
class If:
    source_span: SourceSpan
    test: Expr
    body: list[Stmt]
    orelse: list[Stmt]
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.IF, "source_span": self.source_span.to_jv(),
                                  "test": expr_to_jv(self.test),
                                  "body": [stmt_to_jv(s) for s in self.body],
                                  "orelse": [stmt_to_jv(s) for s in self.orelse]}
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d

@dataclass
class For:
    source_span: SourceSpan
    target: Expr
    iter_expr: Expr  # JSON key: "iter"
    body: list[Stmt]
    orelse: list[Stmt]
    leading_trivia: Optional[list[TriviaNode]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": K.FOR, "source_span": self.source_span.to_jv(),
                                  "target": expr_to_jv(self.target),
                                  "iter": expr_to_jv(self.iter_expr),
                                  "body": [stmt_to_jv(s) for s in self.body],
                                  "orelse": [stmt_to_jv(s) for s in self.orelse]}
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        return d

@dataclass
class While:
    source_span: SourceSpan
    test: Expr
    body: list[Stmt]
    orelse: list[Stmt]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": K.WHILE, "source_span": self.source_span.to_jv(),
                "test": expr_to_jv(self.test),
                "body": [stmt_to_jv(s) for s in self.body],
                "orelse": [stmt_to_jv(s) for s in self.orelse]}

@dataclass
class With:
    source_span: SourceSpan
    context_expr: Expr   # the expression after 'with' (e.g., open(path, "wb"))
    var_name: str        # the 'as' variable name (e.g., "f")
    body: list[Stmt]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "With", "source_span": self.source_span.to_jv(),
                "context_expr": expr_to_jv(self.context_expr),
                "var_name": self.var_name,
                "body": [stmt_to_jv(s) for s in self.body]}

@dataclass
class FunctionDef:
    source_span: SourceSpan
    name: str
    original_name: str
    arg_types: dict[str, str]
    arg_order: list[str]
    arg_defaults: dict[str, JsonVal]
    arg_index: dict[str, int]
    return_type: str
    renamed_symbols: dict[str, str]
    docstring: Optional[str]
    body: list[Stmt]
    is_generator: int
    yield_value_type: str
    vararg_name: Optional[str] = None
    vararg_type: Optional[str] = None
    decorators: Optional[list[str]] = None
    node_meta: Optional[dict[str, JsonVal]] = None
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": K.FUNCTION_DEF, "source_span": self.source_span.to_jv(),
            "name": self.name, "original_name": self.original_name,
            "arg_types": dict(self.arg_types), "arg_order": list(self.arg_order),
            "arg_defaults": dict(self.arg_defaults), "arg_index": dict(self.arg_index),
            "return_type": self.return_type, "renamed_symbols": dict(self.renamed_symbols),
            "docstring": self.docstring,
            "body": [stmt_to_jv(s) for s in self.body],
            "is_generator": self.is_generator, "yield_value_type": self.yield_value_type,
        }
        if self.vararg_name is not None:
            d["vararg_name"] = self.vararg_name
            d["vararg_type"] = self.vararg_type if self.vararg_type is not None else "unknown"
        if self.decorators is not None:
            d["decorators"] = list(self.decorators)
        if self.node_meta is not None:
            d["meta"] = dict(self.node_meta)
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        return d

@dataclass
class ClassDef:
    source_span: SourceSpan
    name: str
    original_name: str
    base: Optional[str]
    body: list[Stmt]
    dataclass_flag: bool
    field_types: dict[str, str]
    node_meta: Optional[dict[str, JsonVal]] = None
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": K.CLASS_DEF, "source_span": self.source_span.to_jv(),
            "name": self.name, "original_name": self.original_name,
            "base": self.base, "dataclass": self.dataclass_flag,
            "field_types": dict(self.field_types),
            "body": [stmt_to_jv(s) for s in self.body],
        }
        if self.node_meta is not None:
            d["meta"] = dict(self.node_meta)
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        return d


@dataclass
class TypeAlias:
    source_span: SourceSpan
    name: str
    value: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "TypeAlias", "source_span": self.source_span.to_jv(),
                "name": self.name}

Stmt = Union[
    Import, ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Swap, Return, Yield, Raise, Pass,
    If, For, While, With, Try, FunctionDef, ClassDef, TypeAlias,
]

def stmt_to_jv(s: Stmt) -> dict[str, JsonVal]:
    return s.to_jv()


# ---------------------------------------------------------------------------
# Module (root)
# ---------------------------------------------------------------------------

@dataclass
class Module:
    source_path: str
    source_span: SourceSpan
    body: list[Stmt]
    main_guard_body: list[Stmt]
    meta: dict[str, JsonVal]
    renamed_symbols: dict[str, str]
    east_stage: int = 1
    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": K.MODULE, "source_path": self.source_path,
            "source_span": self.source_span.to_jv(),
            "body": [stmt_to_jv(s) for s in self.body],
            "main_guard_body": [stmt_to_jv(s) for s in self.main_guard_body],
            "renamed_symbols": dict(self.renamed_symbols),
            "meta": dict(self.meta),
            "east_stage": self.east_stage,
        }
