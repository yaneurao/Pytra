"""EAST node kind string constants (selfhost-safe).

Centralizes the "kind" discriminator strings used across compile/ and optimize/.
"""

from __future__ import annotations

# --- top-level ---
MODULE: str = "Module"

# --- definitions ---
FUNCTION_DEF: str = "FunctionDef"
CLOSURE_DEF: str = "ClosureDef"
CLASS_DEF: str = "ClassDef"
VAR_DECL: str = "VarDecl"

# --- statements ---
ASSIGN: str = "Assign"
ANN_ASSIGN: str = "AnnAssign"
AUG_ASSIGN: str = "AugAssign"
EXPR: str = "Expr"
RETURN: str = "Return"
YIELD: str = "Yield"
IF: str = "If"
WHILE: str = "While"
FOR: str = "For"
FOR_RANGE: str = "ForRange"
FOR_CORE: str = "ForCore"
TRY: str = "Try"
WITH: str = "With"
BREAK: str = "Break"
CONTINUE: str = "Continue"
SWAP: str = "Swap"
TUPLE_UNPACK: str = "TupleUnpack"
MULTI_ASSIGN: str = "MultiAssign"

# --- expressions ---
NAME: str = "Name"
CONSTANT: str = "Constant"
CALL: str = "Call"
ATTRIBUTE: str = "Attribute"
SUBSCRIPT: str = "Subscript"
BIN_OP: str = "BinOp"
UNARY_OP: str = "UnaryOp"
COMPARE: str = "Compare"
IF_EXP: str = "IfExp"
LIST: str = "List"
DICT: str = "Dict"
SET: str = "Set"
TUPLE: str = "Tuple"
LIST_COMP: str = "ListComp"

# --- import ---
IMPORT_FROM: str = "ImportFrom"

# --- pattern matching ---
MATCH: str = "Match"
VARIANT_PATTERN: str = "VariantPattern"
PATTERN_BIND: str = "PatternBind"
PATTERN_WILDCARD: str = "PatternWildcard"

# --- unbox / cast / boundary ---
BOX: str = "Box"
UNBOX: str = "Unbox"
CAST_OR_RAISE: str = "CastOrRaise"
STARRED: str = "Starred"

# --- boolean ---
BOOL_OP: str = "BoolOp"
COVARIANT_COPY: str = "CovariantCopy"

# --- type predicates ---
IS_INSTANCE: str = "IsInstance"
IS_SUBCLASS: str = "IsSubclass"
IS_SUBTYPE: str = "IsSubtype"
TYPE_PREDICATE_CALL: str = "TypePredicateCall"

# --- object boundary ops ---
OBJ_TYPE_ID: str = "ObjTypeId"
OBJ_BOOL: str = "ObjBool"
OBJ_LEN: str = "ObjLen"
OBJ_STR: str = "ObjStr"
OBJ_ITER_INIT: str = "ObjIterInit"
OBJ_ITER_NEXT: str = "ObjIterNext"

# --- iteration plans ---
STATIC_RANGE_FOR_PLAN: str = "StaticRangeForPlan"
RUNTIME_ITER_FOR_PLAN: str = "RuntimeIterForPlan"

# --- target plans ---
NAME_TARGET: str = "NameTarget"
TUPLE_TARGET: str = "TupleTarget"
EXPR_TARGET: str = "ExprTarget"

# --- nominal ADT lowered kinds ---
NOMINAL_ADT_CTOR_CALL: str = "NominalAdtCtorCall"
NOMINAL_ADT_PROJECTION: str = "NominalAdtProjection"
NOMINAL_ADT_VARIANT_PATTERN: str = "NominalAdtVariantPattern"
NOMINAL_ADT_PATTERN_BIND: str = "NominalAdtPatternBind"
NOMINAL_ADT_MATCH: str = "NominalAdtMatch"

# --- JSON decode ---
JSON_DECODE_CALL: str = "JsonDecodeCall"
BUILTIN_CALL: str = "BuiltinCall"

# --- dict lowered ops ---
DICT_GET_MAYBE: str = "DictGetMaybe"
DICT_GET_DEFAULT: str = "DictGetDefault"
DICT_POP: str = "DictPop"
DICT_POP_DEFAULT: str = "DictPopDefault"

# --- type expression kinds ---
NAMED_TYPE: str = "NamedType"
GENERIC_TYPE: str = "GenericType"
DYNAMIC_TYPE: str = "DynamicType"
NOMINAL_ADT_TYPE: str = "NominalAdtType"
OPTIONAL_TYPE: str = "OptionalType"
UNION_TYPE: str = "UnionType"

# --- kind groups ---
LOOP_KINDS: set[str] = {FOR, FOR_RANGE, FOR_CORE, WHILE}
CONTROL_FLOW_KINDS: set[str] = {IF, WHILE, FOR, FOR_CORE, TRY, WITH}
ASSIGNMENT_KINDS: set[str] = {ASSIGN, ANN_ASSIGN, AUG_ASSIGN}
