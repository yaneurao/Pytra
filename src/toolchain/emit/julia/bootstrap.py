"""Bootstrap helpers for the toolchain2 Julia emitter.

These helpers keep the current migration path explicit:
- normalize toolchain2 EAST3 into the legacy Julia emitter's expected shape
- bridge the prepared document into the existing legacy emitter
"""

from __future__ import annotations

import copy

from pytra.std.json import JsonVal

from toolchain.emit.common.code_emitter import RuntimeMapping
from toolchain.link.expand_defaults import expand_cross_module_defaults


def _str_list(value: JsonVal) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
    return out


def _node_uses_name(node: JsonVal, name: str) -> bool:
    if isinstance(node, dict):
        if node.get("kind") == "Name" and node.get("id") == name:
            return True
        for value in node.values():
            if _node_uses_name(value, name):
                return True
        return False
    if isinstance(node, list):
        for item in node:
            if _node_uses_name(item, name):
                return True
        return False
    return False


def _str(node: dict[str, JsonVal], key: str) -> str:
    value = node.get(key)
    if isinstance(value, str):
        return value
    return ""


def _dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    value = node.get(key)
    if isinstance(value, dict):
        return value
    return {}


def module_id_from_doc(east3_doc: dict[str, JsonVal]) -> str:
    meta = _dict(east3_doc, "meta")
    emit_ctx_meta = _dict(meta, "emit_context")
    module_id = _str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _str(meta, "module_id")
    linked = _dict(meta, "linked_program_v1")
    if module_id == "":
        module_id = _str(linked, "module_id")
    return module_id


def prepare_module_for_emit(east3_doc: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]]:
    module_id = module_id_from_doc(east3_doc)
    prepared = copy.deepcopy(east3_doc)
    if module_id != "":
        expand_cross_module_defaults([(module_id, prepared)])
    return module_id, prepared


class JuliaBootstrapRewriter:
    """Normalize toolchain2 EAST3 into the legacy Julia emitter's expected shape."""

    def __init__(self) -> None:
        self.static_attr_globals: dict[str, str] = {}
        self.trait_classes: set[str] = set()
        self.class_bases: dict[str, str] = {}
        self.class_traits: dict[str, set[str]] = {}

    def rewrite_document(self, east3_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
        self._collect_trait_metadata(east3_doc)
        return copy.deepcopy(self._rewrite_node(east3_doc))

    def _parse_implements_decorator(self, decorator: str) -> list[str]:
        if not decorator.startswith("implements(") or not decorator.endswith(")"):
            return []
        inner = decorator[len("implements("):-1].strip()
        if inner == "":
            return []
        out: list[str] = []
        for part in inner.split(","):
            name = part.strip()
            if name != "":
                out.append(name)
        return out

    def _collect_trait_metadata(self, node: JsonVal) -> None:
        if isinstance(node, list):
            for item in node:
                self._collect_trait_metadata(item)
            return
        if not isinstance(node, dict):
            return
        if node.get("kind") == "ClassDef":
            class_name_any = node.get("name")
            if isinstance(class_name_any, str) and class_name_any != "":
                base_any = node.get("base")
                if isinstance(base_any, str) and base_any != "":
                    self.class_bases[class_name_any] = base_any
                decorators = _str_list(node.get("decorators"))
                if "trait" in decorators:
                    self.trait_classes.add(class_name_any)
                implemented: set[str] = set()
                for decorator in decorators:
                    for trait_name in self._parse_implements_decorator(decorator):
                        implemented.add(trait_name)
                if len(implemented) > 0:
                    self.class_traits[class_name_any] = implemented
        for value in node.values():
            self._collect_trait_metadata(value)

    def _trait_closure(self, name: str, visiting: set[str] | None = None) -> set[str]:
        if visiting is None:
            visiting = set()
        if name in visiting:
            return set()
        visiting = set(visiting)
        visiting.add(name)
        out: set[str] = {name}
        base_name = self.class_bases.get(name, "")
        if base_name != "":
            out |= self._trait_closure(base_name, visiting)
        for trait_name in self.class_traits.get(name, set()):
            out |= self._trait_closure(trait_name, visiting)
        return out

    def _class_static_global_name(self, class_name: str, attr_name: str) -> str:
        return "__pytra_cls_" + class_name + "_" + attr_name

    def _rewrite_class_def(self, node: dict[str, JsonVal]) -> list[JsonVal]:
        class_name = node.get("name")
        is_dataclass = node.get("dataclass") is True
        body_any = node.get("body")
        body = body_any if isinstance(body_any, list) else []
        kept_body: list[JsonVal] = []
        lifted_after: list[JsonVal] = []
        for stmt_any in body:
            if not isinstance(stmt_any, dict):
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            stmt_kind = stmt_any.get("kind")
            if stmt_kind not in {"Assign", "AnnAssign"}:
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            if is_dataclass and stmt_kind == "AnnAssign":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            target_any = stmt_any.get("target")
            if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            if not isinstance(class_name, str) or class_name == "":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            attr_name_any = target_any.get("id")
            if not isinstance(attr_name_any, str) or attr_name_any == "":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            global_name = self._class_static_global_name(class_name, attr_name_any)
            self.static_attr_globals[class_name + "." + attr_name_any] = global_name
            lifted_stmt = copy.deepcopy(stmt_any)
            lifted_stmt["target"] = {"kind": "Name", "id": global_name}
            lifted_after.append(self._rewrite_node(lifted_stmt))
        out_class: dict[str, JsonVal] = {}
        for key, value in node.items():
            if key == "body":
                continue
            out_class[key] = self._rewrite_node(value)
        out_class["body"] = kept_body
        out_list: list[JsonVal] = [out_class]
        for stmt in lifted_after:
            out_list.append(stmt)
        return out_list

    def _rewrite_attribute(self, out: dict[str, JsonVal]) -> JsonVal:
        value_any = out.get("value")
        attr_any = out.get("attr")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name" and isinstance(attr_any, str):
            class_name_any = value_any.get("id")
            if isinstance(class_name_any, str):
                global_name = self.static_attr_globals.get(class_name_any + "." + attr_any)
                if isinstance(global_name, str) and global_name != "":
                    return {"kind": "Name", "id": global_name}
        return out

    def _rewrite_function_like(self, node: dict[str, JsonVal], out: dict[str, JsonVal]) -> dict[str, JsonVal]:
        vararg_name_any = node.get("vararg_name")
        if isinstance(vararg_name_any, str) and vararg_name_any != "":
            body_any = node.get("body")
            if _node_uses_name(body_any, vararg_name_any):
                out["vararg_name"] = vararg_name_any
                vararg_type_any = node.get("vararg_type")
                if isinstance(vararg_type_any, str) and vararg_type_any != "":
                    out["vararg_type"] = vararg_type_any
        return out

    def _rewrite_isinstance(self, node: dict[str, JsonVal], out: dict[str, JsonVal]) -> JsonVal:
        expected_name = ""
        expected_any = node.get("expected_type_id")
        if isinstance(expected_any, dict) and expected_any.get("kind") == "Name":
            expected_id = expected_any.get("id")
            if isinstance(expected_id, str):
                expected_name = expected_id
        expected_name_any = node.get("expected_type_name")
        if expected_name == "" and isinstance(expected_name_any, str):
            expected_name = expected_name_any
        value_any = node.get("value")
        resolved_type = ""
        if isinstance(value_any, dict):
            resolved_type_any = value_any.get("resolved_type")
            if isinstance(resolved_type_any, str):
                resolved_type = resolved_type_any.strip()
        if expected_name in self.trait_classes and resolved_type != "" and "|" not in resolved_type:
            implemented_traits = self._trait_closure(resolved_type)
            return {
                "kind": "Constant",
                "value": expected_name in implemented_traits,
                "resolved_type": "bool",
                "repr": "true" if expected_name in implemented_traits else "false",
            }
        return out

    def _rewrite_node(self, node: JsonVal) -> JsonVal:
        if isinstance(node, list):
            out_list: list[JsonVal] = []
            for item in node:
                rewritten = self._rewrite_node(item)
                if isinstance(rewritten, list):
                    for nested in rewritten:
                        out_list.append(nested)
                else:
                    out_list.append(rewritten)
            return out_list
        if not isinstance(node, dict):
            return node
        kind_in = node.get("kind")
        if kind_in == "ClassDef":
            return self._rewrite_class_def(node)
        out: dict[str, JsonVal] = {}
        for key, value in node.items():
            if key in {"vararg_name", "vararg_type", "captures"}:
                continue
            out[key] = self._rewrite_node(value)
        kind = out.get("kind")
        if kind == "ClosureDef":
            out["kind"] = "FunctionDef"
        if kind == "FunctionDef":
            out = self._rewrite_function_like(node, out)
        if kind == "Attribute":
            return self._rewrite_attribute(out)
        if kind == "IsInstance":
            return self._rewrite_isinstance(node, out)
        return out


class JuliaLegacyEmitterBridge:
    """Fallback bridge for Julia bootstrap output.

    The deprecated toolchain_ Julia emitter has been removed from the runtime
    path. Keep the bridge entrypoint, but delegate to the toolchain-native
    subset renderer so callers no longer depend on toolchain_.
    """

    def __init__(self, mapping: RuntimeMapping | None = None) -> None:
        self.mapping = mapping if mapping is not None else RuntimeMapping()

    def emit_module(self, east3_doc: dict[str, JsonVal]) -> str:
        from toolchain.emit.julia.subset import JuliaSubsetRenderer

        meta = east3_doc.get("meta")
        subset_meta = meta if isinstance(meta, dict) else {}
        return JuliaSubsetRenderer(self.mapping, subset_meta).render_module(east3_doc)
