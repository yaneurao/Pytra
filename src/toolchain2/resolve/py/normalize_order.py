"""Post-processing: normalize JSON field ordering to match golden files.

The golden east2 files have a specific field ordering convention.
This module reorders fields to match.

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from pytra.std.json import JsonVal


# Expression node field order: resolved_type comes right after source_span
_EXPR_FIELD_ORDER: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
]

# Name-specific trailing fields
_NAME_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr", "id",
    "type_expr",
]

# Constant-specific trailing fields
_CONSTANT_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr", "value",
]

# BinOp
_BINOP_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "left", "op", "right",
]

# UnaryOp
_UNARYOP_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "op", "operand",
]

# Compare
_COMPARE_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "left", "ops", "comparators",
]

# Call
_CALL_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "func", "args", "keywords",
    # Runtime fields come after keywords
    "lowered_kind", "builtin_name", "runtime_call",
    "resolved_runtime_call", "resolved_runtime_source",
    "runtime_module_id", "runtime_symbol", "runtime_call_adapter_kind",
    "semantic_tag",
    "runtime_owner",
]

# Attribute
_ATTRIBUTE_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "value", "attr",
]

# Subscript
_SUBSCRIPT_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "value", "slice",
]

# List
_LIST_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "elements",
]

# Dict
_DICT_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "keys", "values",
]

# Set
_SET_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "elements",
]

# Tuple
_TUPLE_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "elements",
]

# IfExp
_IFEXP_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "test", "body", "orelse",
]

# BoolOp
_BOOLOP_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "op", "values",
]

# ListComp
_LISTCOMP_FIELDS: list[str] = [
    "kind", "source_span", "resolved_type", "casts", "borrow_kind", "repr",
    "elt", "generators",
]

# FunctionDef
_FUNCDEF_FIELDS: list[str] = [
    "kind", "source_span", "name", "original_name",
    "arg_types", "arg_order", "arg_defaults", "arg_index",
    "return_type", "arg_usage", "renamed_symbols", "docstring",
    "body", "is_generator", "yield_value_type",
    "arg_type_exprs", "return_type_expr",
    "leading_comments", "leading_trivia",
]

# ClassDef
_CLASSDEF_FIELDS: list[str] = [
    "kind", "source_span", "name", "original_name", "base",
    "dataclass", "field_types",
    "bases", "decorators", "body",
    "class_storage_hint",
    "leading_comments", "leading_trivia",
]

# ForRange
_FORRANGE_FIELDS: list[str] = [
    "kind", "source_span", "target", "target_type",
    "start", "stop", "step", "range_mode",
    "body", "orelse",
]

# Assign
_ASSIGN_FIELDS: list[str] = [
    "kind", "source_span", "target", "targets", "value",
    "declare", "decl_type",
    "declare_init",
]

# AnnAssign
_ANNASSIGN_FIELDS: list[str] = [
    "kind", "source_span", "target", "annotation", "value",
    "declare", "decl_type",
    "annotation_type_expr", "decl_type_expr",
    "simple",
]

# AugAssign
_AUGASSIGN_FIELDS: list[str] = [
    "kind", "source_span", "target", "op", "value",
    "declare", "decl_type",
]

# Import resolution section
_IMPORT_RESOLUTION_FIELDS: list[str] = [
    "schema_version", "bindings", "qualified_refs",
]

# Meta section
_META_FIELDS: list[str] = [
    "parser_backend",
    "import_resolution",
    "import_bindings", "qualified_symbol_refs",
    "import_modules", "import_symbols",
    "dispatch_mode",
]

# Module
_MODULE_FIELDS: list[str] = [
    "kind", "source_path", "source_span", "body", "main_guard_body",
    "renamed_symbols", "meta", "east_stage", "schema_version",
]


_KIND_FIELDS: dict[str, list[str]] = {
    "Name": _NAME_FIELDS,
    "Constant": _CONSTANT_FIELDS,
    "BinOp": _BINOP_FIELDS,
    "UnaryOp": _UNARYOP_FIELDS,
    "Compare": _COMPARE_FIELDS,
    "Call": _CALL_FIELDS,
    "Attribute": _ATTRIBUTE_FIELDS,
    "Subscript": _SUBSCRIPT_FIELDS,
    "List": _LIST_FIELDS,
    "Dict": _DICT_FIELDS,
    "Set": _SET_FIELDS,
    "Tuple": _TUPLE_FIELDS,
    "IfExp": _IFEXP_FIELDS,
    "BoolOp": _BOOLOP_FIELDS,
    "ListComp": _LISTCOMP_FIELDS,
    "FunctionDef": _FUNCDEF_FIELDS,
    "ClassDef": _CLASSDEF_FIELDS,
    "For": ["kind", "source_span", "target", "target_type",
            "iter_mode", "iter_source_type", "iter_element_type",
            "iter", "body", "orelse"],
    "ForRange": _FORRANGE_FIELDS,
    "Assign": _ASSIGN_FIELDS,
    "AnnAssign": _ANNASSIGN_FIELDS,
    "AugAssign": _AUGASSIGN_FIELDS,
    "Module": _MODULE_FIELDS,
}


def normalize_field_order(doc: JsonVal, parent_key: str = "") -> JsonVal:
    """Recursively normalize field ordering in a JSON document."""
    if isinstance(doc, dict):
        kind = doc.get("kind")
        if isinstance(kind, str) and kind in _KIND_FIELDS:
            ordered = _reorder_dict(doc, _KIND_FIELDS[kind])
        elif parent_key == "meta":
            ordered = _reorder_dict(doc, _META_FIELDS)
        elif parent_key == "import_resolution":
            ordered = _reorder_dict(doc, _IMPORT_RESOLUTION_FIELDS)
        else:
            ordered = doc
        # Recursively process all values
        result: dict[str, JsonVal] = {}
        for k, v in ordered.items():
            result[k] = normalize_field_order(v, parent_key=k)
        return result
    if isinstance(doc, list):
        return [normalize_field_order(item, parent_key=parent_key) for item in doc]
    return doc


def _reorder_dict(d: dict[str, JsonVal], field_order: list[str]) -> dict[str, JsonVal]:
    """Reorder dict keys according to field_order, preserving extra keys at end."""
    out: dict[str, JsonVal] = {}
    # Add fields in specified order
    for key in field_order:
        if key in d:
            out[key] = d[key]
    # Add remaining fields not in the specified order
    for key in d:
        if key not in out:
            out[key] = d[key]
    return out
