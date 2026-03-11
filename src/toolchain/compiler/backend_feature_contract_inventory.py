"""Representative cross-backend feature inventory for parity-contract work."""

from __future__ import annotations

import re
from typing import Final, TypedDict


CATEGORY_ORDER: Final[tuple[str, ...]] = ("syntax", "builtin", "stdlib")

SUPPORT_STATE_ORDER: Final[tuple[str, ...]] = (
    "supported",
    "fail_closed",
    "not_started",
    "experimental",
)

CATEGORY_NAMING_RULES: Final[dict[str, str]] = {
    "syntax": "syntax.<area>.<feature>",
    "builtin": "builtin.<domain>.<feature>",
    "stdlib": "stdlib.<module>.<feature>",
}

SUPPORT_STATE_CRITERIA: Final[dict[str, str]] = {
    "supported": "Representative fixture and regression lane are expected to pass on the backend without preview-only caveats.",
    "fail_closed": "The backend does not claim feature support but must stop with an explicit unsupported/not-implemented diagnostic instead of silently degrading.",
    "not_started": "No representative implementation or fail-closed lane has been committed yet; the feature may not be claimed in parity summaries.",
    "experimental": "A preview-only or opt-in lane exists, but the feature is not yet treated as stable support in parity summaries.",
}

FAIL_CLOSED_DETAIL_CATEGORIES: Final[tuple[str, ...]] = (
    "not_implemented",
    "unsupported_by_design",
    "preview_only",
    "blocked",
)

FAIL_CLOSED_PHASE_RULES: Final[dict[str, str]] = {
    "parse_and_ir": "Unsupported syntax / frontend lanes must stop before emit instead of coercing the source into an alternate construct.",
    "emit_and_runtime": "Unsupported backend lanes must emit a known-block diagnostic instead of degrading into object/String/comment fallback output.",
    "preview_rollout": "Preview-only lanes must stay in support_state=experimental and may not be reported as supported.",
}

FORBIDDEN_SILENT_FALLBACK_LABELS: Final[tuple[str, ...]] = (
    "object_fallback",
    "string_fallback",
    "comment_stub_fallback",
    "empty_output_fallback",
)

NEW_FEATURE_ACCEPTANCE_RULES: Final[dict[str, str]] = {
    "feature_id_required": "Every new syntax / builtin / stdlib feature must declare a feature ID or explicitly state why it is out of representative scope.",
    "inventory_or_followup_required": "A representative fixture entry or an explicit follow-up parity task must be recorded before merge.",
    "cxx_only_not_complete": "C++ support alone may merge as parity-incomplete work, but it must not close the feature contract by itself.",
    "noncpp_state_required": "At least one non-C++ backend support state must be recorded at merge time, even if that state is fail_closed or not_started.",
    "unsupported_lanes_fail_closed": "Any backend lane that is not marked supported must be explicitly fail_closed, not_started, or experimental; silent fallback is forbidden.",
    "docs_mirror_required": "The docs/en mirror must be updated in the same change that modifies the parity contract.",
}

CATEGORY_ID_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    category: re.compile("^" + rule.replace(".", r"\.").replace("<", "(?P<").replace(">", ">[a-z0-9_]+)") + "$")
    for category, rule in CATEGORY_NAMING_RULES.items()
}


class FeatureInventoryEntry(TypedDict):
    feature_id: str
    category: str
    title: str
    representative_fixture: str
    rationale: str


REPRESENTATIVE_FEATURE_INVENTORY: Final[tuple[FeatureInventoryEntry, ...]] = (
    {
        "feature_id": "syntax.assign.tuple_destructure",
        "category": "syntax",
        "title": "tuple destructuring assignment",
        "representative_fixture": "test/fixtures/core/tuple_assign.py",
        "rationale": "Representative multi-target assignment/destructure lane in the parser and emitters.",
    },
    {
        "feature_id": "syntax.expr.lambda",
        "category": "syntax",
        "title": "lambda expression",
        "representative_fixture": "test/fixtures/core/lambda_basic.py",
        "rationale": "Expression-level closure and call lowering representative.",
    },
    {
        "feature_id": "syntax.expr.list_comprehension",
        "category": "syntax",
        "title": "list comprehension",
        "representative_fixture": "test/fixtures/collections/comprehension.py",
        "rationale": "Representative comprehension parsing/lowering lane.",
    },
    {
        "feature_id": "syntax.control.for_range",
        "category": "syntax",
        "title": "for-range loop",
        "representative_fixture": "test/fixtures/control/for_range.py",
        "rationale": "Representative control-flow loop syntax that also exercises builtin range lowering.",
    },
    {
        "feature_id": "syntax.control.try_raise",
        "category": "syntax",
        "title": "try/raise/finally flow",
        "representative_fixture": "test/fixtures/control/try_raise.py",
        "rationale": "Representative exception syntax and control-flow lane.",
    },
    {
        "feature_id": "syntax.oop.virtual_dispatch",
        "category": "syntax",
        "title": "inheritance and virtual dispatch",
        "representative_fixture": "test/fixtures/oop/inheritance_virtual_dispatch_multilang.py",
        "rationale": "Representative class/inheritance syntax that already has multi-backend fixture usage.",
    },
    {
        "feature_id": "builtin.iter.range",
        "category": "builtin",
        "title": "range builtin",
        "representative_fixture": "test/fixtures/control/for_range.py",
        "rationale": "Representative integer iteration builtin across parse/lowering/emit lanes.",
    },
    {
        "feature_id": "builtin.iter.enumerate",
        "category": "builtin",
        "title": "enumerate builtin",
        "representative_fixture": "test/fixtures/strings/enumerate_basic.py",
        "rationale": "Representative iterable helper builtin with tuple item semantics.",
    },
    {
        "feature_id": "builtin.iter.zip",
        "category": "builtin",
        "title": "zip builtin",
        "representative_fixture": "test/fixtures/signature/ok_generator_tuple_target.py",
        "rationale": "Representative multi-iterable builtin that also feeds tuple-target semantics.",
    },
    {
        "feature_id": "builtin.type.isinstance",
        "category": "builtin",
        "title": "isinstance builtin",
        "representative_fixture": "test/fixtures/oop/is_instance.py",
        "rationale": "Representative type-predicate builtin used by multiple backends and runtime contracts.",
    },
    {
        "feature_id": "builtin.bit.invert_and_mask",
        "category": "builtin",
        "title": "bitwise invert and mask operators",
        "representative_fixture": "test/fixtures/typing/bitwise_invert_basic.py",
        "rationale": "Representative unary and binary bitwise builtin/operator lane shared across targets.",
    },
    {
        "feature_id": "stdlib.json.loads_dumps",
        "category": "stdlib",
        "title": "pytra.std.json decode/encode",
        "representative_fixture": "test/fixtures/stdlib/json_extended.py",
        "rationale": "Representative nominal runtime module with decode-first behavior and container parity concerns.",
    },
    {
        "feature_id": "stdlib.pathlib.path_ops",
        "category": "stdlib",
        "title": "pytra.std.pathlib path operations",
        "representative_fixture": "test/fixtures/stdlib/pathlib_extended.py",
        "rationale": "Representative filesystem-oriented stdlib surface with path object methods.",
    },
    {
        "feature_id": "stdlib.enum.enum_and_intflag",
        "category": "stdlib",
        "title": "pytra.std.enum Enum/IntFlag",
        "representative_fixture": "test/fixtures/stdlib/enum_extended.py",
        "rationale": "Representative stdlib enum surface with flags and operator interactions.",
    },
    {
        "feature_id": "stdlib.argparse.parse_args",
        "category": "stdlib",
        "title": "pytra.std.argparse parse args",
        "representative_fixture": "test/fixtures/stdlib/argparse_extended.py",
        "rationale": "Representative CLI-facing stdlib module with structured object output.",
    },
    {
        "feature_id": "stdlib.math.imported_symbols",
        "category": "stdlib",
        "title": "pytra.std.math imported symbols",
        "representative_fixture": "test/fixtures/stdlib/pytra_std_import_math.py",
        "rationale": "Representative stdlib imported-symbol lane shared by multiple emitters.",
    },
    {
        "feature_id": "stdlib.re.sub",
        "category": "stdlib",
        "title": "pytra.std.re sub",
        "representative_fixture": "test/fixtures/stdlib/re_extended.py",
        "rationale": "Representative regex stdlib helper with direct runtime binding.",
    },
)


def iter_representative_feature_inventory() -> tuple[FeatureInventoryEntry, ...]:
    return REPRESENTATIVE_FEATURE_INVENTORY
