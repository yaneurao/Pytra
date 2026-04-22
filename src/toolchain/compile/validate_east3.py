"""EAST3 invariant validator."""

from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compile.jv import JsonVal, Node, jv_str, jv_int, jv_is_int, jv_is_dict, jv_is_list, jv_dict, jv_list


@dataclass
class ValidationResult:
    source_path: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


def _count_residual_for(node: JsonVal) -> int:
    count: int = 0
    if jv_is_dict(node):
        node_dict: Node = jv_dict(node)
        kind = jv_str(node_dict.get("kind", ""))
        if kind == "For" or kind == "ForRange":
            count += 1
        for _, value in node_dict.items():
            count += _count_residual_for(value)
    elif jv_is_list(node):
        for item in jv_list(node):
            count += _count_residual_for(item)
    return count


def validate_east3(doc: Node) -> ValidationResult:
    result = ValidationResult()
    result.source_path = "" + jv_str(doc.get("source_path", ""))

    stage = doc.get("east_stage")
    if not jv_is_int(stage) or jv_int(stage) != 3:
        result.errors.append("east_stage is " + str(stage) + ", expected 3")

    sv = doc.get("schema_version")
    if not jv_is_int(sv) or jv_int(sv) != 1:
        result.errors.append("schema_version is " + str(sv) + ", expected 1")

    residual_for: int = _count_residual_for(doc)
    if residual_for > 0:
        result.errors.append("residual For/ForRange nodes: " + str(residual_for) + " (must be lowered to ForCore)")
    result.stats["residual_for"] = residual_for

    result.stats["object_resolved_type"] = 0
    return result



def format_result(result: ValidationResult) -> str:
    lines: list[str] = []
    status = "PASS" if len(result.errors) == 0 else "FAIL"
    lines.append(status + ": " + result.source_path)
    for err in result.errors:
        lines.append("  ERROR: " + err)
    count = result.stats.get("object_resolved_type", 0)
    lines.append("  object_resolved_type: " + str(count))
    return "\n".join(lines)
