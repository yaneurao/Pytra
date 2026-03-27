from pytra.std.json import JsonVal


def read_kind(node: JsonVal) -> str:
    if not isinstance(node, dict):
        return ""
    kind = node.get("kind")
    if isinstance(kind, str) and kind.strip() != "":
        return kind.strip()
    return ""


def collect_names(doc: dict[str, JsonVal]) -> list[str]:
    names: list[str] = []
    body = doc.get("body")
    if not isinstance(body, list):
        return names
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        if stmt.get("kind") != "FunctionDef":
            continue
        name = stmt.get("name")
        if isinstance(name, str):
            names.append(name)
    return names


def owner_name(owner: JsonVal) -> str:
    owner_node = owner if isinstance(owner, dict) else None
    if owner_node is None:
        return ""
    name = owner_node.get("name")
    return name if isinstance(name, str) else ""


def reassign_then_check(node: JsonVal, other: JsonVal) -> str:
    if isinstance(node, dict):
        name = node.get("name")
        node = other
        if isinstance(node, dict):
            other_name = node.get("name")
            if isinstance(other_name, str):
                return other_name
        return name if isinstance(name, str) else ""
    return ""
