"""EAST node kind string constants (selfhost-safe).

Centralizes the "kind" discriminator strings used across compile/ and optimize/.
"""

from __future__ import annotations

# --- top-level ---
MODULE: str = "Module"

# --- definitions ---
FUNCTION_DEF: str = "FunctionDef"
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

# --- unbox / cast ---
UNBOX: str = "Unbox"
CAST_OR_RAISE: str = "CastOrRaise"

# --- iteration plans ---
STATIC_RANGE_FOR_PLAN: str = "StaticRangeForPlan"
RUNTIME_ITER_FOR_PLAN: str = "RuntimeIterForPlan"

# --- target plans ---
NAME_TARGET: str = "NameTarget"
TUPLE_TARGET: str = "TupleTarget"

# --- dict lowered ops ---
DICT_GET_MAYBE: str = "DictGetMaybe"
DICT_GET_DEFAULT: str = "DictGetDefault"
DICT_POP: str = "DictPop"
DICT_POP_DEFAULT: str = "DictPopDefault"

# --- kind groups ---
LOOP_KINDS: set[str] = {FOR, FOR_RANGE, FOR_CORE, WHILE}
CONTROL_FLOW_KINDS: set[str] = {IF, WHILE, FOR, FOR_CORE, TRY, WITH}
ASSIGNMENT_KINDS: set[str] = {ASSIGN, ANN_ASSIGN, AUG_ASSIGN}
