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

from toolchain.common import kinds as K
from toolchain.parse.py.source_span import SourceSpan, NULL_SPAN


# selfhost C++ header generation cannot represent Python Union aliases like
# Expr = Union[...] in field declarations. Field declarations use JsonVal directly.


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
    args: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "GenericType", "base": self.base, "args": self.args}

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

TriviaNodeNode = Union[TriviaBlank, TriviaComment]


# ---------------------------------------------------------------------------
# Import alias
# ---------------------------------------------------------------------------

@dataclass
class ImportAlias:
    name: str
    asname: str
    def to_jv(self) -> dict[str, JsonVal]:
        asname: JsonVal = None
        if self.asname != "":
            asname = self.asname
        return {"name": self.name, "asname": asname}


# ---------------------------------------------------------------------------
# Semantic sub-structures
# ---------------------------------------------------------------------------

@dataclass
class Keyword:
    arg: Optional[str]
    value_node: JsonVal  # forward ref
    def to_jv(self) -> dict[str, JsonVal]:
        return {"arg": self.arg, "value": expr_to_jv(self.value_node)}

@dataclass
class Comprehension:
    target: JsonVal
    iter_expr: JsonVal
    ifs: list[JsonVal]
    is_async: bool
    def to_jv(self) -> dict[str, JsonVal]:
        return {"target": expr_to_jv(self.target), "iter": expr_to_jv(self.iter_expr),
                "ifs": _expr_jv_list(self.ifs), "is_async": self.is_async}

@dataclass
class DictEntry:
    key: JsonVal
    value: JsonVal
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
    casts: list[JsonVal] = []
    return {
        "source_span": e.source_span.to_jv(),
        "casts": casts,
        "borrow_kind": "value",
        "repr": e.repr_text,
    }

def _expr_jv_list(values: list[JsonVal]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for value in values:
        out.append(expr_to_jv(value))
    return out

def _stmt_jv_list(values: list[JsonVal]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for value in values:
        out.append(stmt_to_jv(value))
    return out

def _str_jv_list(values: list[str]) -> list[JsonVal]:
    out: list[JsonVal] = []
    for value in values:
        out.append(value)
    return out

def _str_dict_jv(values: dict[str, str]) -> dict[str, JsonVal]:
    out: dict[str, JsonVal] = {}
    for key, value in values.items():
        out[key] = value
    return out

def _int_dict_jv(values: dict[str, int]) -> dict[str, JsonVal]:
    out: dict[str, JsonVal] = {}
    for key, value in values.items():
        out[key] = value
    return out


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class Name:
    base: ExprBase
    id: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Name"}
        d.update(_expr_base_jv(self.base))
        d["id"] = self.id
        return d

@dataclass
class Constant:
    base: ExprBase
    value: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Constant"}
        d.update(_expr_base_jv(self.base))
        d["value"] = self.value
        return d

@dataclass
class BinOp:
    base: ExprBase
    left: JsonVal
    op: str
    right: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "BinOp"}
        d.update(_expr_base_jv(self.base))
        d["left"] = expr_to_jv(self.left)
        d["op"] = self.op
        d["right"] = expr_to_jv(self.right)
        return d

@dataclass
class UnaryOp:
    base: ExprBase
    op: str
    operand: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "UnaryOp"}
        d.update(_expr_base_jv(self.base))
        d["op"] = self.op
        d["operand"] = expr_to_jv(self.operand)
        return d

@dataclass
class BoolOp:
    base: ExprBase
    op: str
    values: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "BoolOp"}
        d.update(_expr_base_jv(self.base))
        d["op"] = self.op
        d["values"] = _expr_jv_list(self.values)
        return d

@dataclass
class Compare:
    base: ExprBase
    left: JsonVal
    ops: list[str]
    comparators: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Compare"}
        d.update(_expr_base_jv(self.base))
        d["left"] = expr_to_jv(self.left)
        d["ops"] = _str_jv_list(self.ops)
        d["comparators"] = _expr_jv_list(self.comparators)
        return d

@dataclass
class Call:
    base: ExprBase
    func: JsonVal
    args: list[JsonVal]
    keywords: list[Keyword]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Call"}
        d.update(_expr_base_jv(self.base))
        d["func"] = expr_to_jv(self.func)
        d["args"] = _expr_jv_list(self.args)
        keywords: list[JsonVal] = []
        for kw in self.keywords:
            keywords.append(kw.to_jv())
        d["keywords"] = keywords
        return d

@dataclass
class Attribute:
    base: ExprBase
    value: JsonVal
    attr: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Attribute"}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        d["attr"] = self.attr
        return d

@dataclass
class Subscript:
    base: ExprBase
    value: JsonVal
    slice_expr: JsonVal
    is_slice: bool = False
    lowered_kind: Optional[str] = None
    lower: JsonVal = None
    upper: JsonVal = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Subscript"}
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
    lower: JsonVal
    upper: JsonVal
    step: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Slice",
                "lower": expr_to_jv(self.lower) if self.lower is not None else None,
                "upper": expr_to_jv(self.upper) if self.upper is not None else None,
                "step": expr_to_jv(self.step) if self.step is not None else None}

@dataclass
class IfExp:
    base: ExprBase
    test: JsonVal
    body: JsonVal
    orelse: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "IfExp"}
        d.update(_expr_base_jv(self.base))
        d["test"] = expr_to_jv(self.test)
        d["body"] = expr_to_jv(self.body)
        d["orelse"] = expr_to_jv(self.orelse)
        return d

@dataclass
class ListExpr:
    base: ExprBase
    elements: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "List"}
        d.update(_expr_base_jv(self.base))
        d["elements"] = _expr_jv_list(self.elements)
        return d

@dataclass
class TupleExpr:
    base: ExprBase
    elements: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Tuple"}
        d.update(_expr_base_jv(self.base))
        d["elements"] = _expr_jv_list(self.elements)
        return d

@dataclass
class SetExpr:
    base: ExprBase
    elements: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Set"}
        d.update(_expr_base_jv(self.base))
        d["elements"] = _expr_jv_list(self.elements)
        return d

@dataclass
class DictExpr:
    base: ExprBase
    keys: list[JsonVal]
    dict_values: list[JsonVal]
    entries: list[DictEntry] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Dict"}
        d.update(_expr_base_jv(self.base))
        if len(self.entries) > 0:
            entries: list[JsonVal] = []
            for entry in self.entries:
                entries.append(entry.to_jv())
            d["entries"] = entries
        else:
            d["keys"] = _expr_jv_list(self.keys)
            d["values"] = _expr_jv_list(self.dict_values)
        return d

@dataclass
class ListComp:
    base: ExprBase
    elt: JsonVal
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "ListComp"}
        d.update(_expr_base_jv(self.base))
        d["elt"] = expr_to_jv(self.elt)
        generators: list[JsonVal] = []
        for gen in self.generators:
            generators.append(gen.to_jv())
        d["generators"] = generators
        return d

@dataclass
class FStringText:
    """f-string 内のリテラルテキスト部分 (borrow_kind/casts なし)。"""
    source_span: SourceSpan
    repr_text: str
    value: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Constant", "source_span": self.source_span.to_jv(),
                "repr": self.repr_text, "value": self.value}

@dataclass
class FormattedValue:
    value: JsonVal
    format_spec: Optional[str] = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "FormattedValue", "value": expr_to_jv(self.value)}
        if self.format_spec is not None:
            d["format_spec"] = self.format_spec
        return d

@dataclass
class JoinedStr:
    base: ExprBase
    values: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "JoinedStr"}
        d.update(_expr_base_jv(self.base))
        d["values"] = self.values
        return d

@dataclass
class LambdaArg:
    name: str
    default_expr: JsonVal = None
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "arg", "arg": self.name, "annotation": None}
        if self.default_expr is not None:
            d["default"] = expr_to_jv(self.default_expr)
        return d

@dataclass
class LambdaExpr:
    base: ExprBase
    args: list[LambdaArg]
    body: JsonVal
    return_type: str
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Lambda"}
        d.update(_expr_base_jv(self.base))
        args: list[JsonVal] = []
        for arg in self.args:
            args.append(arg.to_jv())
        d["args"] = args
        d["body"] = expr_to_jv(self.body)
        d["return_type"] = self.return_type
        return d

@dataclass
class RangeExpr:
    base: ExprBase
    start: JsonVal
    stop: JsonVal
    step: JsonVal
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
    elt: JsonVal
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "SetComp"}
        d.update(_expr_base_jv(self.base))
        d["elt"] = expr_to_jv(self.elt)
        generators: list[JsonVal] = []
        for gen in self.generators:
            generators.append(gen.to_jv())
        d["generators"] = generators
        return d

@dataclass
class DictComp:
    base: ExprBase
    key: JsonVal
    value: JsonVal
    generators: list[Comprehension]
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "DictComp"}
        d.update(_expr_base_jv(self.base))
        d["key"] = expr_to_jv(self.key)
        d["value"] = expr_to_jv(self.value)
        generators: list[JsonVal] = []
        for gen in self.generators:
            generators.append(gen.to_jv())
        d["generators"] = generators
        return d

@dataclass
class Starred:
    base: ExprBase
    value: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Starred"}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        return d

ExprNode = Union[
    Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute,
    Subscript, SliceExpr, IfExp, ListExpr, SetExpr, TupleExpr, DictExpr,
    ListComp, SetComp, DictComp, JoinedStr,
    RangeExpr, LambdaExpr, Starred,
]

def expr_to_jv(e: JsonVal) -> dict[str, JsonVal]:
    if isinstance(e, dict):
        return e
    return e.to_jv()


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class Import:
    source_span: SourceSpan
    names: list[ImportAlias]
    def to_jv(self) -> dict[str, JsonVal]:
        names: list[JsonVal] = []
        for name in self.names:
            names.append(name.to_jv())
        return {"kind": "Import", "source_span": self.source_span.to_jv(),
                "names": names}

@dataclass
class ImportFrom:
    source_span: SourceSpan
    module: str
    names: list[ImportAlias]
    level: int
    def to_jv(self) -> dict[str, JsonVal]:
        names: list[JsonVal] = []
        for name in self.names:
            names.append(name.to_jv())
        return {"kind": "ImportFrom", "source_span": self.source_span.to_jv(),
                "module": self.module, "names": names, "level": self.level}

@dataclass
class AnnAssign:
    source_span: SourceSpan
    target: JsonVal
    annotation: str
    value: JsonVal
    declare: bool
    node_meta: dict[str, JsonVal] = field(default_factory=dict)
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "AnnAssign", "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target), "annotation": self.annotation,
            "value": expr_to_jv(self.value) if self.value is not None else None,
            "declare": self.declare,
        }
        if len(self.node_meta) > 0:
            d["meta"] = dict(self.node_meta)
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        return d

@dataclass
class Assign:
    source_span: SourceSpan
    target: JsonVal
    value: JsonVal
    declare: bool
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "Assign", "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target), "value": expr_to_jv(self.value),
            "declare": self.declare,
        }
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        return d

@dataclass
class AugAssign:
    source_span: SourceSpan
    target: JsonVal
    op: str
    value: JsonVal
    declare: bool
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "AugAssign", "source_span": self.source_span.to_jv(),
                "target": expr_to_jv(self.target), "op": self.op,
                "value": expr_to_jv(self.value), "declare": self.declare}

@dataclass
class ExprStmt:
    source_span: SourceSpan
    value: JsonVal
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Expr", "source_span": self.source_span.to_jv(),
                                  "value": expr_to_jv(self.value)}
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        return d

@dataclass
class Swap:
    source_span: SourceSpan
    left: JsonVal
    right: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Swap", "source_span": self.source_span.to_jv(),
                "left": expr_to_jv(self.left), "right": expr_to_jv(self.right)}

@dataclass
class Return:
    source_span: SourceSpan
    value: JsonVal
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Return", "source_span": self.source_span.to_jv(),
                                  "value": expr_to_jv(self.value) if self.value is not None else None}
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        return d

@dataclass
class Yield:
    source_span: SourceSpan
    value: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Yield", "source_span": self.source_span.to_jv(),
                "value": expr_to_jv(self.value)}

@dataclass
class Raise:
    source_span: SourceSpan
    exc: JsonVal
    cause: JsonVal
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Raise", "source_span": self.source_span.to_jv(),
                "exc": expr_to_jv(self.exc) if self.exc is not None else None,
                "cause": expr_to_jv(self.cause) if self.cause is not None else None}

@dataclass
class ExceptHandler:
    exc_type_expr: JsonVal
    name: Optional[str]
    body: list[JsonVal]
    source_span: SourceSpan
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "ExceptHandler",
                "type": expr_to_jv(self.exc_type_expr) if self.exc_type_expr is not None else None,
                "name": self.name,
                "body": _stmt_jv_list(self.body)}

@dataclass
class Try:
    source_span: SourceSpan
    body: list[JsonVal]
    handlers: list[ExceptHandler]
    orelse: list[JsonVal]
    finalbody: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        handlers: list[JsonVal] = []
        for handler in self.handlers:
            handlers.append(handler.to_jv())
        d: dict[str, JsonVal] = {"kind": "Try", "source_span": self.source_span.to_jv(),
                "body": _stmt_jv_list(self.body),
                "handlers": handlers,
                "orelse": _stmt_jv_list(self.orelse),
                "finalbody": _stmt_jv_list(self.finalbody)}
        return d

@dataclass
class Pass:
    source_span: SourceSpan
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "Pass", "source_span": self.source_span.to_jv()}

@dataclass
class If:
    source_span: SourceSpan
    test: JsonVal
    body: list[JsonVal]
    orelse: list[JsonVal]
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "If", "source_span": self.source_span.to_jv(),
                                  "test": expr_to_jv(self.test),
                                  "body": _stmt_jv_list(self.body),
                                  "orelse": _stmt_jv_list(self.orelse)}
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        return d

@dataclass
class For:
    source_span: SourceSpan
    target: JsonVal
    iter_expr: JsonVal  # JSON key: "iter"
    body: list[JsonVal]
    orelse: list[JsonVal]
    leading_trivia: list[JsonVal] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "For", "source_span": self.source_span.to_jv(),
                                  "target": expr_to_jv(self.target),
                                  "iter": expr_to_jv(self.iter_expr),
                                  "body": _stmt_jv_list(self.body),
                                  "orelse": _stmt_jv_list(self.orelse)}
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        return d

@dataclass
class While:
    source_span: SourceSpan
    test: JsonVal
    body: list[JsonVal]
    orelse: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "While", "source_span": self.source_span.to_jv(),
                "test": expr_to_jv(self.test),
                "body": _stmt_jv_list(self.body),
                "orelse": _stmt_jv_list(self.orelse)}

@dataclass
class With:
    source_span: SourceSpan
    context_expr: JsonVal   # the expression after 'with' (e.g., open(path, "wb"))
    var_name: str        # the 'as' variable name (e.g., "f")
    body: list[JsonVal]
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "With", "source_span": self.source_span.to_jv(),
                "context_expr": expr_to_jv(self.context_expr),
                "var_name": self.var_name,
                "body": _stmt_jv_list(self.body)}

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
    body: list[JsonVal]
    is_generator: int
    yield_value_type: str
    vararg_name: Optional[str] = None
    vararg_type: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    node_meta: dict[str, JsonVal] = field(default_factory=dict)
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "FunctionDef", "source_span": self.source_span.to_jv(),
            "name": self.name, "original_name": self.original_name,
            "arg_types": _str_dict_jv(self.arg_types), "arg_order": _str_jv_list(self.arg_order),
            "arg_defaults": dict(self.arg_defaults), "arg_index": _int_dict_jv(self.arg_index),
            "return_type": self.return_type, "renamed_symbols": _str_dict_jv(self.renamed_symbols),
            "docstring": self.docstring,
            "body": _stmt_jv_list(self.body),
            "is_generator": self.is_generator, "yield_value_type": self.yield_value_type,
        }
        if self.vararg_name is not None:
            d["vararg_name"] = self.vararg_name
            d["vararg_type"] = self.vararg_type if self.vararg_type is not None else "unknown"
        if len(self.decorators) > 0:
            d["decorators"] = _str_jv_list(self.decorators)
        if len(self.node_meta) > 0:
            d["meta"] = dict(self.node_meta)
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        return d

@dataclass
class ClassDef:
    source_span: SourceSpan
    name: str
    original_name: str
    base: Optional[str]
    body: list[JsonVal]
    dataclass_flag: bool
    field_types: dict[str, str]
    decorators: list[str] = field(default_factory=list)
    node_meta: dict[str, JsonVal] = field(default_factory=dict)
    leading_trivia: list[JsonVal] = field(default_factory=list)
    leading_comments: list[str] = field(default_factory=list)
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "ClassDef", "source_span": self.source_span.to_jv(),
            "name": self.name, "original_name": self.original_name,
            "base": self.base, "dataclass": self.dataclass_flag,
            "field_types": _str_dict_jv(self.field_types),
            "body": _stmt_jv_list(self.body),
        }
        if len(self.decorators) > 0:
            d["decorators"] = _str_jv_list(self.decorators)
        if len(self.node_meta) > 0:
            d["meta"] = dict(self.node_meta)
        if len(self.leading_comments) > 0:
            d["leading_comments"] = _str_jv_list(self.leading_comments)
        if len(self.leading_trivia) > 0:
            d["leading_trivia"] = self.leading_trivia
        return d


@dataclass
class TypeAlias:
    source_span: SourceSpan
    name: str
    value: str
    def to_jv(self) -> dict[str, JsonVal]:
        return {"kind": "TypeAlias", "source_span": self.source_span.to_jv(),
                "name": self.name,
                "value": self.value}

StmtNode = Union[
    Import, ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Swap, Return, Yield, Raise, Pass,
    If, For, While, With, Try, FunctionDef, ClassDef, TypeAlias,
]

def stmt_to_jv(s: JsonVal) -> dict[str, JsonVal]:
    if isinstance(s, dict):
        return s
    return s.to_jv()


# ---------------------------------------------------------------------------
# Module (root)
# ---------------------------------------------------------------------------

@dataclass
class Module:
    source_path: str
    source_span: SourceSpan
    body: list[JsonVal]
    main_guard_body: list[JsonVal]
    meta: dict[str, JsonVal]
    renamed_symbols: dict[str, str]
    east_stage: int = 1
    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {}
        d["kind"] = "Module"
        d["source_path"] = self.source_path
        if not (self.source_span.lineno is None and self.source_span.col is None and self.source_span.end_lineno is None and self.source_span.end_col is None):
            d["source_span"] = self.source_span.to_jv()
        d["body"] = _stmt_jv_list(self.body)
        d["main_guard_body"] = _stmt_jv_list(self.main_guard_body)
        d["renamed_symbols"] = _str_dict_jv(self.renamed_symbols)
        d["meta"] = dict(self.meta)
        d["east_stage"] = self.east_stage
        return d
