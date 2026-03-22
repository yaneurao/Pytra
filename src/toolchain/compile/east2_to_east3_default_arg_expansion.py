"""EAST3 default argument expansion pass.

Expands call sites where positional arguments are fewer than the callee's
parameter count by appending the missing default values from the callee's
``arg_defaults`` dict.

This is a Python semantics transformation: Python allows omitting trailing
arguments that have defaults.  Block-scoped target languages require all
arguments to be present at the call site.
"""

from __future__ import annotations

import copy
from typing import Any


def _collect_function_signatures(module: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Walk the module and collect FunctionDef signatures by name.

    Returns ``{func_name: {"arg_order": [...], "arg_defaults": {...}}}``.
    Also collects class methods as ``ClassName.method_name``.
    """
    sigs: dict[str, dict[str, Any]] = {}
    body = module.get("body")
    if not isinstance(body, list):
        return sigs
    for stmt in body:
        if not isinstance(stmt, dict):
            continue
        _collect_sig(stmt, sigs, class_name="")
    return sigs


def _collect_sig(node: dict[str, Any], sigs: dict[str, dict[str, Any]], class_name: str) -> None:
    kind = node.get("kind", "")
    if kind == "FunctionDef":
        name = node.get("name", "")
        if not isinstance(name, str) or name == "":
            return
        arg_order = node.get("arg_order")
        arg_defaults = node.get("arg_defaults")
        if not isinstance(arg_order, list):
            return
        sig: dict[str, Any] = {
            "arg_order": arg_order,
            "arg_defaults": arg_defaults if isinstance(arg_defaults, dict) else {},
        }
        full_name = class_name + "." + name if class_name != "" else name
        sigs[name] = sig
        if full_name != name:
            sigs[full_name] = sig
        # Recurse into body for nested functions
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig(s, sigs, class_name="")
    elif kind == "ClassDef":
        cls_name = node.get("name", "")
        if not isinstance(cls_name, str):
            cls_name = ""
        body = node.get("body")
        if isinstance(body, list):
            for s in body:
                if isinstance(s, dict):
                    _collect_sig(s, sigs, class_name=cls_name)


def _expand_call_defaults(node: Any, sigs: dict[str, dict[str, Any]]) -> None:
    """Recursively walk and expand default arguments at call sites."""
    if isinstance(node, list):
        for item in node:
            _expand_call_defaults(item, sigs)
        return
    if not isinstance(node, dict):
        return
    nd: dict[str, Any] = node

    if nd.get("kind") == "Call":
        func = nd.get("func")
        callee_name = ""
        if isinstance(func, dict):
            if func.get("kind") == "Name":
                callee_name = func.get("id", "")
            elif func.get("kind") == "Attribute":
                # For method calls, try just the method name
                callee_name = func.get("attr", "")

        if isinstance(callee_name, str) and callee_name != "" and callee_name in sigs:
            sig = sigs[callee_name]
            arg_order = sig["arg_order"]
            arg_defaults = sig["arg_defaults"]
            args = nd.get("args")
            if isinstance(args, list) and isinstance(arg_order, list) and isinstance(arg_defaults, dict):
                n_args = len(args)
                # Filter out 'self' from param count
                effective_params = [p for p in arg_order if isinstance(p, str) and p != "self"]
                n_effective = len(effective_params)
                # Collect keyword argument names to avoid duplicates
                kw_names: set[str] = set()
                keywords = nd.get("keywords")
                if isinstance(keywords, list):
                    for kw in keywords:
                        if isinstance(kw, dict):
                            kw_arg = kw.get("arg")
                            if isinstance(kw_arg, str) and kw_arg != "":
                                kw_names.add(kw_arg)
                if n_args < n_effective and len(arg_defaults) > 0:
                    # Append missing default values (skip if already in keywords)
                    for i in range(n_args, n_effective):
                        param_name = effective_params[i]
                        if param_name in kw_names:
                            continue  # Already provided as keyword arg
                        if param_name in arg_defaults:
                            default_node = arg_defaults[param_name]
                            if isinstance(default_node, dict):
                                args.append(copy.deepcopy(default_node))

    # Recurse into all children
    for value in nd.values():
        if isinstance(value, (dict, list)):
            _expand_call_defaults(value, sigs)


def expand_default_arguments(module: dict[str, Any]) -> dict[str, Any]:
    """Top-level entry: expand default arguments at call sites.

    Mutates *module* in place and returns it.
    """
    sigs = _collect_function_signatures(module)
    if len(sigs) > 0:
        _expand_call_defaults(module, sigs)
    return module
