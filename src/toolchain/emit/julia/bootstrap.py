"""Bootstrap helpers for the toolchain2 Julia emitter.

These helpers keep the current migration path explicit:
- normalize toolchain2 EAST3 into the legacy Julia emitter's expected shape
- bridge the prepared document into the existing legacy emitter
"""

from __future__ import annotations

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


def _bs_str(node: dict[str, JsonVal], key: str) -> str:
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
    module_id = _bs_str(emit_ctx_meta, "module_id")
    if module_id == "":
        module_id = _bs_str(meta, "module_id")
    linked = _dict(meta, "linked_program_v1")
    if module_id == "":
        module_id = _bs_str(linked, "module_id")
    return module_id


def prepare_module_for_emit(east3_doc: dict[str, JsonVal]) -> tuple[str, dict[str, JsonVal]]:
    module_id = module_id_from_doc(east3_doc)
    prepared = east3_doc
    if module_id != "":
        modules_for_defaults: list[JsonVal] = [prepared]
        expand_cross_module_defaults(modules_for_defaults)
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
        rewritten = self._rewrite_node(east3_doc)
        if isinstance(rewritten, dict):
            return rewritten
        return {}

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
            class_name = _bs_str(node, "name")
            if class_name != "":
                base_name = _bs_str(node, "base")
                if base_name != "":
                    self.class_bases[class_name] = base_name
                decorators = _str_list(node.get("decorators"))
                if "trait" in decorators:
                    self.trait_classes.add(class_name)
                implemented: set[str] = set()
                for decorator in decorators:
                    for trait_name in self._parse_implements_decorator(decorator):
                        implemented.add(trait_name)
                if len(implemented) > 0:
                    self.class_traits[class_name] = implemented
        for value in node.values():
            self._collect_trait_metadata(value)

    def _trait_closure(self, name: str, visiting: set[str] | None = None) -> set[str]:
        active_visiting: set[str] = set()
        if visiting is not None:
            for visited_name in visiting:
                active_visiting.add(visited_name)
        return self._trait_closure_inner(name, active_visiting)

    def _trait_closure_inner(self, name: str, visiting: set[str]) -> set[str]:
        if name in visiting:
            empty: set[str] = set()
            return empty
        visiting.add(name)
        out: set[str] = {name}
        base_name = self.class_bases.get(name, "")
        if base_name != "":
            for closed_name in self._trait_closure_inner(base_name, visiting):
                out.add(closed_name)
        direct_traits: set[str] = set()
        if name in self.class_traits:
            direct_traits = self.class_traits[name]
        for trait_name in direct_traits:
            for closed_name in self._trait_closure_inner(trait_name, visiting):
                out.add(closed_name)
        return out

    def _class_static_global_name(self, class_name: str, attr_name: str) -> str:
        return "__pytra_cls_" + class_name + "_" + attr_name

    def _rewrite_class_def(self, node: dict[str, JsonVal]) -> list[JsonVal]:
        class_name = _bs_str(node, "name")
        is_dataclass = False
        is_dataclass_raw = node.get("dataclass")
        if isinstance(is_dataclass_raw, bool):
            is_dataclass = is_dataclass_raw
        body_any = node.get("body")
        body = body_any if isinstance(body_any, list) else []
        kept_body: list[JsonVal] = []
        lifted_after: list[JsonVal] = []
        for stmt_any in body:
            if not isinstance(stmt_any, dict):
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            stmt_kind = _bs_str(stmt_any, "kind")
            if stmt_kind != "Assign" and stmt_kind != "AnnAssign":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            if is_dataclass and stmt_kind == "AnnAssign":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            target_any = stmt_any.get("target")
            if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            if class_name == "":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            attr_name = _bs_str(target_any, "id")
            if attr_name == "":
                kept_body.append(self._rewrite_node(stmt_any))
                continue
            global_name = self._class_static_global_name(class_name, attr_name)
            self.static_attr_globals[class_name + "." + attr_name] = global_name
            lifted_stmt: dict[str, JsonVal] = {}
            for key, value in stmt_any.items():
                lifted_stmt[key] = value
            target_node: dict[str, JsonVal] = {}
            target_node["kind"] = "Name"
            target_node["id"] = global_name
            lifted_stmt["target"] = target_node
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
            class_name = _bs_str(value_any, "id")
            if class_name != "":
                global_name = self.static_attr_globals.get(class_name + "." + attr_any)
                if global_name != "":
                    out_node: dict[str, JsonVal] = {}
                    out_node["kind"] = "Name"
                    out_node["id"] = global_name
                    return out_node
        return out

    def _rewrite_function_like(self, node: dict[str, JsonVal], out: dict[str, JsonVal]) -> dict[str, JsonVal]:
        vararg_name = _bs_str(node, "vararg_name")
        if vararg_name != "":
            body_any = node.get("body")
            if _node_uses_name(body_any, vararg_name):
                out["vararg_name"] = vararg_name
                vararg_type = _bs_str(node, "vararg_type")
                if vararg_type != "":
                    out["vararg_type"] = vararg_type
        return out

    def _rewrite_isinstance(self, node: dict[str, JsonVal], out: dict[str, JsonVal]) -> JsonVal:
        expected_name = ""
        expected_any = node.get("expected_type_id")
        if isinstance(expected_any, dict) and _bs_str(expected_any, "kind") == "Name":
            expected_name = _bs_str(expected_any, "id")
        if expected_name == "":
            expected_name = _bs_str(node, "expected_type_name")
        value_any = node.get("value")
        resolved_type = ""
        if isinstance(value_any, dict):
            resolved_type = _bs_str(value_any, "resolved_type").strip()
        if expected_name in self.trait_classes and resolved_type != "" and "|" not in resolved_type:
            implemented_traits = self._trait_closure(resolved_type)
            matched = expected_name in implemented_traits
            const_node: dict[str, JsonVal] = {}
            const_node["kind"] = "Constant"
            const_node["value"] = matched
            const_node["resolved_type"] = "bool"
            const_node["repr"] = "true" if matched else "false"
            return const_node
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
