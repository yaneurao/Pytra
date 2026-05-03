from __future__ import annotations

import unittest

from toolchain.emit.powershell.emitter import emit_ps1_module


def _name(value: str, resolved_type: str = "unknown") -> dict[str, object]:
    return {"kind": "Name", "id": value, "resolved_type": resolved_type}


def _field_factory(factory: dict[str, object], resolved_type: str) -> dict[str, object]:
    return {
        "kind": "Unbox",
        "resolved_type": resolved_type,
        "value": {
            "kind": "Call",
            "func": _name("field"),
            "args": [],
            "keywords": [{"arg": "default_factory", "value": factory}],
        },
    }


def _ann(name: str, resolved_type: str, value: object) -> dict[str, object]:
    return {
        "kind": "AnnAssign",
        "target": {"kind": "Name", "id": name, "resolved_type": resolved_type},
        "annotation": resolved_type,
        "value": value,
    }


def _module(body: list[object]) -> dict[str, object]:
    return {
        "kind": "Module",
        "meta": {
            "module_id": "test.power",
            "emit_context": {"module_id": "test.power", "root_rel_prefix": ""},
        },
        "body": body,
    }


def _module_with_meta(body: list[object], meta: dict[str, object]) -> dict[str, object]:
    doc = _module(body)
    base_meta = doc["meta"]
    assert isinstance(base_meta, dict)
    base_meta.update(meta)
    return doc


class PowerShellDataclassFieldDefaultTests(unittest.TestCase):
    def test_type_alias_subscript_assignment_is_comment_only(self) -> None:
        doc = _module([
            {
                "kind": "Assign",
                "target": {"kind": "Name", "id": "Node", "resolved_type": "unknown"},
                "value": {
                    "kind": "Subscript",
                    "value": _name("dict", "type"),
                    "slice": {
                        "kind": "Tuple",
                        "elements": [_name("str", "type"), _name("JsonVal", "unknown")],
                    },
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("# type alias: Node", ps1)
        self.assertNotIn("$Node = $dict", ps1)

    def test_path_cwd_static_call_uses_runtime_mapping_without_receiver(self) -> None:
        doc = _module([
            {
                "kind": "FunctionDef",
                "name": "repo",
                "arg_order": [],
                "body": [
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "func": {
                                "kind": "Attribute",
                                "value": _name("Path", "unknown"),
                                "attr": "cwd",
                            },
                            "args": [],
                            "keywords": [],
                        },
                    },
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("return ,((Path_cwd))", ps1)
        self.assertNotIn("(cwd)", ps1)

    def test_path_instance_methods_use_runtime_mapping_for_unknown_receivers(self) -> None:
        doc = _module([
            {
                "kind": "FunctionDef",
                "name": "has_src",
                "arg_order": ["cwd"],
                "body": [
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "func": {
                                "kind": "Attribute",
                                "value": {
                                    "kind": "Call",
                                    "func": {
                                        "kind": "Attribute",
                                        "value": _name("cwd", "unknown"),
                                        "attr": "joinpath",
                                    },
                                    "args": [{"kind": "Constant", "value": "src"}],
                                    "keywords": [],
                                },
                                "attr": "exists",
                            },
                            "args": [],
                            "keywords": [],
                        },
                    },
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn('return ,((Path_exists (Path_joinpath $cwd "src")))', ps1)
        self.assertNotIn('$cwd.joinpath("src").exists()', ps1)

    def test_sys_argv_tail_uses_powershell_script_args(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "cli_argv", "resolved_type": "list[str]"},
                "annotation": "list[str]",
                "value": {
                    "kind": "Subscript",
                    "value": {
                        "kind": "Attribute",
                        "value": _name("sys", "module"),
                        "attr": "argv",
                        "runtime_module_id": "pytra.std.sys",
                    },
                    "slice": {
                        "kind": "Slice",
                        "lower": {"kind": "Constant", "value": 1},
                        "upper": None,
                        "step": None,
                    },
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$cli_argv = (__pytra_list $args)", ps1)
        self.assertNotIn("$argv", ps1)

    def test_imported_function_call_is_not_treated_as_callable_variable(self) -> None:
        doc = _module_with_meta(
            [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "exit_code", "resolved_type": "int64"},
                    "annotation": "int64",
                    "value": {
                        "kind": "Call",
                        "func": _name("run_emit_cli", "callable"),
                        "args": [{"kind": "Constant", "value": None}],
                        "keywords": [],
                    },
                },
            ],
            {
                "import_bindings": [
                    {
                        "local_name": "run_emit_cli",
                        "resolved_binding_kind": "symbol",
                        "runtime_symbol_kind": "function",
                    }
                ]
            },
        )

        ps1 = emit_ps1_module(doc)

        self.assertIn("$exit_code = (run_emit_cli $null)", ps1)
        self.assertNotIn("& $run_emit_cli", ps1)

    def test_callable_decl_type_assignment_invokes_via_variable(self) -> None:
        doc = _module([
            {
                "kind": "FunctionDef",
                "name": "run",
                "arg_order": ["direct_emit_fn", "east_doc", "output_dir"],
                "arg_types": {
                    "direct_emit_fn": "Callable[[dict[str, JsonVal], Path],int64]",
                    "east_doc": "dict[str,JsonVal]",
                    "output_dir": "Path",
                },
                "body": [
                    {
                        "kind": "Assign",
                        "target": {
                            "kind": "Name",
                            "id": "active_direct_emit_fn",
                            "resolved_type": "unknown",
                        },
                        "declare": True,
                        "decl_type": "Callable[[dict[str, JsonVal], Path],int64]",
                        "value": _name("direct_emit_fn", "Callable[[dict[str, JsonVal], Path],int64]"),
                    },
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "func": _name("active_direct_emit_fn", "unknown"),
                            "args": [_name("east_doc", "dict[str,JsonVal]"), _name("output_dir", "Path")],
                            "keywords": [],
                        },
                    },
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$active_direct_emit_fn = $direct_emit_fn", ps1)
        self.assertIn("return ,((& $active_direct_emit_fn $east_doc $output_dir))", ps1)
        self.assertNotIn("(active_direct_emit_fn $east_doc $output_dir)", ps1)

    def test_json_value_and_container_methods_use_runtime_helpers(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "obj", "resolved_type": "unknown"},
                "annotation": "unknown",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": {
                            "kind": "Call",
                            "func": _name("JsonValue", "type"),
                            "args": [_name("raw", "unknown")],
                            "keywords": [],
                        },
                        "attr": "as_obj",
                    },
                    "args": [],
                    "keywords": [],
                },
            },
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "name", "resolved_type": "str"},
                "annotation": "str",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": _name("obj", "unknown"),
                        "attr": "get_str",
                    },
                    "args": [{"kind": "Constant", "value": "name"}],
                    "keywords": [],
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$obj = (JsonValue_as_obj (JsonValue $raw))", ps1)
        self.assertIn('$name = (JsonObj_get_str $obj "name")', ps1)
        self.assertNotIn(".as_obj()", ps1)
        self.assertNotIn(".get_str(", ps1)

    def test_json_module_alias_loads_obj_uses_runtime_helper(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "raw_obj", "resolved_type": "unknown"},
                "annotation": "unknown",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": {
                            "kind": "Name",
                            "id": "json",
                            "resolved_type": "module",
                            "runtime_module_id": "pytra.std.json",
                        },
                        "attr": "loads_obj",
                    },
                    "args": [_name("text", "str")],
                    "keywords": [],
                    "resolved_runtime_call": "json.loads_obj",
                    "runtime_module_id": "pytra.std.json",
                    "runtime_symbol": "loads_obj",
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$raw_obj = (__pytra_json_loads_obj $text)", ps1)
        self.assertNotIn("(loads_obj $text)", ps1)

    def test_unknown_dict_items_uses_hashtable_enumerator(self) -> None:
        doc = _module([
            {
                "kind": "FunctionDef",
                "name": "pairs",
                "arg_order": ["info_obj"],
                "body": [
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "func": {
                                "kind": "Attribute",
                                "value": {
                                    "kind": "Attribute",
                                    "value": _name("info_obj", "unknown"),
                                    "attr": "raw",
                                },
                                "attr": "items",
                            },
                            "args": [],
                            "keywords": [],
                        },
                    },
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn('return ,((@((__pytra_getattr $info_obj "raw").GetEnumerator() | ForEach-Object { ,@($_.Key, $_.Value) })))', ps1)
        self.assertNotIn('.items()', ps1)

    def test_dict_get_preserves_empty_list_default_in_if_subexpression(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "cached", "resolved_type": "list[str]"},
                "annotation": "list[str]",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": _name("cache", "dict[str,list[str]]"),
                        "attr": "get",
                    },
                    "args": [_name("key", "str"), {"kind": "List", "elements": []}],
                    "keywords": [],
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("{ ,($cache[$key]) }", ps1)
        self.assertIn("{ ,(([System.Collections.Generic.List[object]]::new())) }", ps1)

    def test_collection_ifexp_preserves_empty_list_branch(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "cached", "resolved_type": "list[str]"},
                "annotation": "list[str]",
                "value": {
                    "kind": "IfExp",
                    "resolved_type": "list[unknown]",
                    "test": _name("use_cache", "bool"),
                    "body": _name("existing", "list[str]"),
                    "orelse": {"kind": "List", "elements": []},
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("{ ,($existing) }", ps1)
        self.assertIn("{ ,(([System.Collections.Generic.List[object]]::new())) }", ps1)

    def test_unknown_string_strip_call_uses_runtime_helper(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "tail", "resolved_type": "str"},
                "annotation": "str",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": {
                            "kind": "Call",
                            "func": {
                                "kind": "Attribute",
                                "value": {"kind": "Constant", "value": "", "resolved_type": "str"},
                                "attr": "join",
                            },
                            "args": [_name("current", "list[str]")],
                            "keywords": [],
                        },
                        "attr": "strip",
                    },
                    "args": [],
                    "keywords": [],
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn('$tail = (__pytra_str_strip (__pytra_str_join "" $current))', ps1)
        self.assertNotIn(".strip()", ps1)

    def test_unknown_string_predicate_call_uses_runtime_helper(self) -> None:
        doc = _module([
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "is_digit", "resolved_type": "bool"},
                "annotation": "bool",
                "value": {
                    "kind": "Call",
                    "func": {
                        "kind": "Attribute",
                        "value": {
                            "kind": "Subscript",
                            "value": _name("safe", "str"),
                            "slice": {"kind": "Constant", "value": 0},
                            "resolved_type": "unknown",
                        },
                        "attr": "isdigit",
                    },
                    "args": [],
                    "keywords": [],
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$is_digit = (__pytra_str_isdigit ([string]$safe[0]))", ps1)
        self.assertNotIn(".isdigit()", ps1)

    def test_list_returning_call_uses_null_safe_return_temp(self) -> None:
        doc = _module([
            {
                "kind": "FunctionDef",
                "name": "cr_list",
                "arg_order": ["node", "key"],
                "return_type": "list[JsonVal]",
                "body": [
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Call",
                            "resolved_type": "list[JsonVal]",
                            "func": _name("_list", "callable"),
                            "args": [_name("node", "dict[str,JsonVal]"), _name("key", "str")],
                            "keywords": [],
                        },
                    },
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$__pytra_return_value = (& $_list $node $key)", ps1)
        self.assertIn("if ($null -eq $__pytra_return_value) { $__pytra_return_value = ([System.Collections.Generic.List[object]]::new()) }", ps1)
        self.assertIn("return ,($__pytra_return_value)", ps1)

    def test_list_assignment_from_call_uses_null_safe_empty_list_guard(self) -> None:
        doc = _module([
            {
                "kind": "Assign",
                "target": {"kind": "Name", "id": "ops", "resolved_type": "unknown"},
                "declare": True,
                "decl_type": "list[JsonVal]",
                "value": {
                    "kind": "Call",
                    "resolved_type": "list[JsonVal]",
                    "func": _name("_list", "callable"),
                    "args": [_name("node", "dict[str,JsonVal]"), {"kind": "Constant", "value": "ops"}],
                    "keywords": [],
                },
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertIn("$__pytra_list_value = (& $_list $node \"ops\")", ps1)
        self.assertIn("if ($null -eq $__pytra_list_value) { $ops = ([System.Collections.Generic.List[object]]::new()) }", ps1)
        self.assertIn("else { $ops = @($__pytra_list_value) }", ps1)

    def test_dataclass_default_factory_lowers_to_constructor_defaults(self) -> None:
        doc = _module([
            {
                "kind": "ClassDef",
                "name": "RuntimeMapping",
                "dataclass": True,
                "field_types": {
                    "calls": "dict[str,str]",
                    "items": "list[str]",
                    "seen": "set[str]",
                    "prefix": "str",
                },
                "body": [
                    _ann("calls", "dict[str,str]", _field_factory(_name("dict", "type"), "dict[str,str]")),
                    _ann("items", "list[str]", _field_factory(_name("list", "type"), "list[str]")),
                    _ann("seen", "set[str]", _field_factory(_name("set", "type"), "set[str]")),
                    _ann("prefix", "str", {"kind": "Constant", "value": "__pytra_"}),
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertNotIn("$calls = (field $dict)", ps1)
        self.assertNotIn("$items = (field $list)", ps1)
        self.assertNotIn("$seen = (field $set)", ps1)
        self.assertIn("$calls = @{}", ps1)
        self.assertIn("$items = ([System.Collections.Generic.List[object]]::new())", ps1)
        self.assertIn("$seen = (__pytra_set)", ps1)
        self.assertIn('$prefix = "__pytra_"', ps1)

    def test_dataclass_default_factory_supports_lambda_and_class_factories(self) -> None:
        lambda_factory = {
            "kind": "Lambda",
            "args": [],
            "body": {
                "kind": "List",
                "elements": [{"kind": "Dict", "keys": [], "values": []}],
            },
        }
        doc = _module([
            {
                "kind": "ClassDef",
                "name": "Child",
                "dataclass": True,
                "field_types": {},
                "body": [],
            },
            {
                "kind": "ClassDef",
                "name": "Parent",
                "dataclass": True,
                "field_types": {"child": "Child", "scopes": "list[dict[str,str]]"},
                "body": [
                    _ann("child", "Child", _field_factory(_name("Child", "type"), "Child")),
                    _ann("scopes", "list[dict[str,str]]", _field_factory(lambda_factory, "list[dict[str,str]]")),
                ],
            },
        ])

        ps1 = emit_ps1_module(doc)

        self.assertNotIn("$child = (field $Child)", ps1)
        self.assertIn('$child = $($__obj = @{}; Child $__obj; $__obj)', ps1)
        self.assertIn("$scopes = (__pytra_mklist @{})", ps1)


if __name__ == "__main__":
    unittest.main()
