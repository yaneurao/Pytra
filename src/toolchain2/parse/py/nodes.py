"""EAST1 ノード定義: dataclass ベース。

§5.1: Any/object 禁止、全フィールド具象型。
§5.2: Python 標準モジュール直接 import 禁止 (typing, dataclasses は例外)。

JSON シリアライズは pytra.std.json.JsonVal を使う。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from toolchain2.parse.py.source_span import SourceSpan, NULL_SPAN

# JsonVal は pytra.std.json で定義されているが、toolchain2 からは
# 型注釈としてのみ使う。実体は再帰的 Union:
#   None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
# ここではシリアライズ用に同等の型エイリアスを定義する。
JsonVal = Union[None, bool, int, float, str, list["JsonVal"], dict[str, "JsonVal"]]


# ---------------------------------------------------------------------------
# Type expression nodes (型注釈用)
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
        return {
            "kind": "GenericType",
            "base": self.base,
            "args": [a.to_jv() for a in self.args],
        }


TypeExpr = Union[NamedType, GenericType]


def type_expr_to_jv(te: TypeExpr) -> dict[str, JsonVal]:
    return te.to_jv()


# ---------------------------------------------------------------------------
# Trivia nodes (空行・コメント)
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
# Semantic sub-structures (dict[str, object] の代わり)
# ---------------------------------------------------------------------------

@dataclass
class Cast:
    """型キャスト情報。"""
    operand: str       # "left" | "right"
    from_type: str     # JSON key: "from"
    to_type: str       # JSON key: "to"
    reason: str

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "operand": self.operand,
            "from": self.from_type,
            "to": self.to_type,
            "reason": self.reason,
        }


@dataclass
class Keyword:
    """関数呼び出しのキーワード引数。"""
    arg: str
    value_node: Expr  # forward ref

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "arg": self.arg,
            "value": expr_to_jv(self.value_node),
        }


@dataclass
class Comprehension:
    """リスト内包表記の generator。"""
    target: Expr  # forward ref
    iter_expr: Expr  # forward ref
    ifs: list[Expr]  # forward ref
    is_async: bool

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "target": expr_to_jv(self.target),
            "iter": expr_to_jv(self.iter_expr),
            "ifs": [expr_to_jv(e) for e in self.ifs],
            "is_async": self.is_async,
        }
        return d


@dataclass
class DictEntry:
    """Dict リテラルのエントリ。"""
    key: Expr  # forward ref
    value: Expr  # forward ref

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "key": expr_to_jv(self.key),
            "value": expr_to_jv(self.value),
        }


# ModuleMeta は JSON 互換の dict で保持する。
# meta 構造は parser_backend, import_resolution, import_bindings,
# qualified_symbol_refs, import_modules, import_symbols を含む
# 複雑な入れ子で、個別 dataclass にするよりも dict[str, JsonVal] が実用的。


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class ExprBase:
    """式ノードの共通フィールド。"""
    source_span: SourceSpan
    resolved_type: str
    casts: list[Cast]
    borrow_kind: str
    repr_text: str  # JSON 出力時のキーは "repr"


def _expr_base_jv(e: ExprBase) -> dict[str, JsonVal]:
    return {
        "source_span": e.source_span.to_jv(),
        "resolved_type": e.resolved_type,
        "casts": [c.to_jv() for c in e.casts],
        "borrow_kind": e.borrow_kind,
        "repr": e.repr_text,
    }


@dataclass
class Name:
    base: ExprBase
    id: str
    type_expr: Optional[TypeExpr] = None
    iter_element_type: Optional[str] = None
    iter_protocol: Optional[str] = None
    iterable_trait: Optional[str] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Name"}
        d.update(_expr_base_jv(self.base))
        d["id"] = self.id
        if self.type_expr is not None:
            d["type_expr"] = self.type_expr.to_jv()
        if self.iter_element_type is not None:
            d["iter_element_type"] = self.iter_element_type
        if self.iter_protocol is not None:
            d["iter_protocol"] = self.iter_protocol
        if self.iterable_trait is not None:
            d["iterable_trait"] = self.iterable_trait
        return d


@dataclass
class Constant:
    base: ExprBase
    value: Union[int, float, str, bool]

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Constant"}
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
    operand: Expr

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
        d: dict[str, JsonVal] = {"kind": "Compare"}
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
    # Optional semantic fields
    builtin_name: Optional[str] = None
    lowered_kind: Optional[str] = None
    runtime_call: Optional[str] = None
    runtime_call_adapter_kind: Optional[str] = None
    runtime_module_id: Optional[str] = None
    runtime_symbol: Optional[str] = None
    semantic_tag: Optional[str] = None
    resolved_runtime_call: Optional[str] = None
    resolved_runtime_source: Optional[str] = None
    runtime_owner: Optional[Expr] = None
    yields_dynamic: Optional[bool] = None
    iter_element_type: Optional[str] = None
    iter_protocol: Optional[str] = None
    iterable_trait: Optional[str] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Call"}
        d.update(_expr_base_jv(self.base))
        d["func"] = expr_to_jv(self.func)
        d["args"] = [expr_to_jv(a) for a in self.args]
        d["keywords"] = [kw.to_jv() for kw in self.keywords]
        if self.builtin_name is not None:
            d["builtin_name"] = self.builtin_name
        if self.lowered_kind is not None:
            d["lowered_kind"] = self.lowered_kind
        if self.runtime_call is not None:
            d["runtime_call"] = self.runtime_call
        if self.runtime_call_adapter_kind is not None:
            d["runtime_call_adapter_kind"] = self.runtime_call_adapter_kind
        if self.runtime_module_id is not None:
            d["runtime_module_id"] = self.runtime_module_id
        if self.runtime_symbol is not None:
            d["runtime_symbol"] = self.runtime_symbol
        if self.semantic_tag is not None:
            d["semantic_tag"] = self.semantic_tag
        if self.resolved_runtime_call is not None:
            d["resolved_runtime_call"] = self.resolved_runtime_call
        if self.resolved_runtime_source is not None:
            d["resolved_runtime_source"] = self.resolved_runtime_source
        if self.runtime_owner is not None:
            d["runtime_owner"] = expr_to_jv(self.runtime_owner)
        if self.yields_dynamic is not None:
            d["yields_dynamic"] = self.yields_dynamic
        if self.iter_element_type is not None:
            d["iter_element_type"] = self.iter_element_type
        if self.iter_protocol is not None:
            d["iter_protocol"] = self.iter_protocol
        if self.iterable_trait is not None:
            d["iterable_trait"] = self.iterable_trait
        return d


@dataclass
class Attribute:
    base: ExprBase
    value: Expr
    attr: str
    type_expr: Optional[TypeExpr] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Attribute"}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        d["attr"] = self.attr
        if self.type_expr is not None:
            d["type_expr"] = self.type_expr.to_jv()
        return d


@dataclass
class Subscript:
    base: ExprBase
    value: Expr
    slice_expr: Expr  # "slice" は Python 予約語ではないが Slice 型と紛らわしいので
    lowered_kind: Optional[str] = None
    lower: Optional[Expr] = None
    upper: Optional[Expr] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Subscript"}
        d.update(_expr_base_jv(self.base))
        d["value"] = expr_to_jv(self.value)
        d["slice"] = expr_to_jv(self.slice_expr)
        if self.lowered_kind is not None:
            d["lowered_kind"] = self.lowered_kind
        if self.lower is not None:
            d["lower"] = expr_to_jv(self.lower)
        if self.upper is not None:
            d["upper"] = expr_to_jv(self.upper)
        return d


@dataclass
class SliceExpr:
    lower: Optional[Expr]
    upper: Optional[Expr]
    step: Optional[Expr]

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "Slice",
            "lower": expr_to_jv(self.lower) if self.lower is not None else None,
            "upper": expr_to_jv(self.upper) if self.upper is not None else None,
            "step": expr_to_jv(self.step) if self.step is not None else None,
        }


@dataclass
class IfExp:
    base: ExprBase
    test: Expr
    body: Expr
    orelse: Expr

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
    elements: list[Expr]

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "List"}
        d.update(_expr_base_jv(self.base))
        d["elements"] = [expr_to_jv(e) for e in self.elements]
        return d


@dataclass
class TupleExpr:
    base: ExprBase
    elements: list[Expr]

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {"kind": "Tuple"}
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
        d: dict[str, JsonVal] = {"kind": "Dict"}
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
        d: dict[str, JsonVal] = {"kind": "ListComp"}
        d.update(_expr_base_jv(self.base))
        d["elt"] = expr_to_jv(self.elt)
        d["generators"] = [g.to_jv() for g in self.generators]
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


# Expr union type
Expr = Union[
    Name, Constant, BinOp, UnaryOp, BoolOp, Compare, Call, Attribute,
    Subscript, SliceExpr, IfExp, ListExpr, TupleExpr, DictExpr, ListComp,
    RangeExpr,
]


def expr_to_jv(e: Expr) -> dict[str, JsonVal]:
    return e.to_jv()


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class ImportFrom:
    source_span: SourceSpan
    module: str
    names: list[ImportAlias]
    level: int

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "ImportFrom",
            "source_span": self.source_span.to_jv(),
            "module": self.module,
            "names": [n.to_jv() for n in self.names],
            "level": self.level,
        }


@dataclass
class AnnAssign:
    source_span: SourceSpan
    target: Expr
    annotation: str
    annotation_type_expr: TypeExpr
    value: Optional[Expr]
    decl_type: str
    decl_type_expr: TypeExpr
    declare: bool
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "AnnAssign",
            "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target),
            "annotation": self.annotation,
            "value": expr_to_jv(self.value) if self.value is not None else None,
            "declare": self.declare,
            "decl_type": self.decl_type,
            "annotation_type_expr": self.annotation_type_expr.to_jv(),
            "decl_type_expr": self.decl_type_expr.to_jv(),
        }
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
    decl_type: Optional[str]
    declare: bool
    declare_init: Optional[bool] = None
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "Assign",
            "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target),
            "value": expr_to_jv(self.value),
            "decl_type": self.decl_type,
            "declare": self.declare,
        }
        if self.declare_init is not None:
            d["declare_init"] = self.declare_init
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
    decl_type: Optional[str]
    declare: bool

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "AugAssign",
            "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target),
            "op": self.op,
            "value": expr_to_jv(self.value),
            "decl_type": self.decl_type,
            "declare": self.declare,
        }


@dataclass
class ExprStmt:
    source_span: SourceSpan
    value: Expr
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "Expr",
            "source_span": self.source_span.to_jv(),
            "value": expr_to_jv(self.value),
        }
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d


@dataclass
class Return:
    source_span: SourceSpan
    value: Expr

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "Return",
            "source_span": self.source_span.to_jv(),
            "value": expr_to_jv(self.value),
        }


@dataclass
class Raise:
    source_span: SourceSpan
    exc: Expr
    cause: Optional[Expr]

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "Raise",
            "source_span": self.source_span.to_jv(),
            "exc": expr_to_jv(self.exc),
            "cause": expr_to_jv(self.cause) if self.cause is not None else None,
        }


@dataclass
class Pass:
    source_span: SourceSpan

    def to_jv(self) -> dict[str, JsonVal]:
        return {
            "kind": "Pass",
            "source_span": self.source_span.to_jv(),
        }


@dataclass
class If:
    source_span: SourceSpan
    test: Expr
    body: list[Stmt]
    orelse: list[Stmt]
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "If",
            "source_span": self.source_span.to_jv(),
            "test": expr_to_jv(self.test),
            "body": [stmt_to_jv(s) for s in self.body],
            "orelse": [stmt_to_jv(s) for s in self.orelse],
        }
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d


@dataclass
class ForRange:
    source_span: SourceSpan
    target: Expr
    target_type: str
    start: Expr
    stop: Expr
    step: Expr
    body: list[Stmt]
    orelse: list[Stmt]
    range_mode: str
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "ForRange",
            "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target),
            "target_type": self.target_type,
            "start": expr_to_jv(self.start),
            "stop": expr_to_jv(self.stop),
            "step": expr_to_jv(self.step),
            "body": [stmt_to_jv(s) for s in self.body],
            "orelse": [stmt_to_jv(s) for s in self.orelse],
            "range_mode": self.range_mode,
        }
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d


@dataclass
class For:
    source_span: SourceSpan
    target: Expr
    target_type: str
    iter_expr: Expr  # JSON key: "iter"
    iter_element_type: str
    iter_mode: str
    iter_source_type: str
    body: list[Stmt]
    orelse: list[Stmt]
    leading_trivia: Optional[list[TriviaNode]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "For",
            "source_span": self.source_span.to_jv(),
            "target": expr_to_jv(self.target),
            "target_type": self.target_type,
            "iter": expr_to_jv(self.iter_expr),
            "iter_element_type": self.iter_element_type,
            "iter_mode": self.iter_mode,
            "iter_source_type": self.iter_source_type,
            "body": [stmt_to_jv(s) for s in self.body],
            "orelse": [stmt_to_jv(s) for s in self.orelse],
        }
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
        return {
            "kind": "While",
            "source_span": self.source_span.to_jv(),
            "test": expr_to_jv(self.test),
            "body": [stmt_to_jv(s) for s in self.body],
            "orelse": [stmt_to_jv(s) for s in self.orelse],
        }


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
    arg_usage: dict[str, str]
    renamed_symbols: dict[str, str]
    docstring: Optional[str]
    body: list[Stmt]
    is_generator: int
    yield_value_type: str
    arg_type_exprs: Optional[dict[str, dict[str, JsonVal]]] = None
    return_type_expr: Optional[TypeExpr] = None
    decorators: Optional[list[str]] = None
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "FunctionDef",
            "source_span": self.source_span.to_jv(),
            "name": self.name,
            "original_name": self.original_name,
            "arg_types": dict(self.arg_types),
            "arg_order": list(self.arg_order),
            "arg_defaults": dict(self.arg_defaults),
            "arg_index": dict(self.arg_index),
            "return_type": self.return_type,
            "arg_usage": dict(self.arg_usage),
            "renamed_symbols": dict(self.renamed_symbols),
            "docstring": self.docstring,
            "body": [stmt_to_jv(s) for s in self.body],
            "is_generator": self.is_generator,
            "yield_value_type": self.yield_value_type,
        }
        if self.arg_type_exprs is not None:
            d["arg_type_exprs"] = dict(self.arg_type_exprs)
        if self.return_type_expr is not None:
            d["return_type_expr"] = self.return_type_expr.to_jv()
        if self.decorators is not None:
            d["decorators"] = list(self.decorators)
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d


@dataclass
class ClassDef:
    source_span: SourceSpan
    name: str
    original_name: str
    base: Optional[str]
    body: list[Stmt]
    dataclass_flag: bool  # JSON key: "dataclass"
    field_types: dict[str, str]
    class_storage_hint: str
    leading_trivia: Optional[list[TriviaNode]] = None
    leading_comments: Optional[list[str]] = None

    def to_jv(self) -> dict[str, JsonVal]:
        d: dict[str, JsonVal] = {
            "kind": "ClassDef",
            "source_span": self.source_span.to_jv(),
            "name": self.name,
            "original_name": self.original_name,
            "base": self.base,
            "body": [stmt_to_jv(s) for s in self.body],
            "dataclass": self.dataclass_flag,
            "field_types": dict(self.field_types),
            "class_storage_hint": self.class_storage_hint,
        }
        if self.leading_trivia is not None:
            d["leading_trivia"] = [t.to_jv() for t in self.leading_trivia]
        if self.leading_comments is not None:
            d["leading_comments"] = list(self.leading_comments)
        return d


# Stmt union type
Stmt = Union[
    ImportFrom, AnnAssign, Assign, AugAssign, ExprStmt, Return, Raise, Pass,
    If, ForRange, For, While, FunctionDef, ClassDef,
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
            "kind": "Module",
            "source_path": self.source_path,
            "source_span": self.source_span.to_jv(),
            "body": [stmt_to_jv(s) for s in self.body],
            "main_guard_body": [stmt_to_jv(s) for s in self.main_guard_body],
            "renamed_symbols": dict(self.renamed_symbols),
            "meta": dict(self.meta),
            "east_stage": self.east_stage,
        }
