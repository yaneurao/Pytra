"""Guard tests for non-cpp EAST3 default/compatibility contract."""

from __future__ import annotations

import copy
import re
import sys
import subprocess
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from backends.cs.emitter import transpile_to_csharp
from backends.go.emitter import transpile_to_go
from backends.java.emitter import transpile_to_java
from backends.kotlin.emitter import transpile_to_kotlin
from backends.nim.emitter import transpile_to_nim
from backends.rs.emitter.rs_emitter import transpile_to_rust
from backends.scala.emitter import transpile_to_scala
from backends.swift.emitter import transpile_to_swift
from toolchain.frontends.type_expr import parse_type_expr_text


def _general_union_module() -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "body": [
            {
                "kind": "FunctionDef",
                "name": "pick",
                "arg_order": ["x"],
                "args": [{"arg": "x"}],
                "arg_types": {"x": "int64|bool"},
                "arg_type_exprs": {"x": parse_type_expr_text("int | bool")},
                "return_type": "int64|bool",
                "return_type_expr": parse_type_expr_text("int | bool"),
                "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x", "resolved_type": "int64|bool"}}],
            }
        ],
        "main_guard_body": [],
        "meta": {},
    }


class NonCppEast3ContractGuardTest(unittest.TestCase):
    def test_noncpp_east3_contract_static_check_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_noncpp_east3_contract.py", "--skip-transpile"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"{cp.stdout}\n{cp.stderr}")
        self.assertIn("static contract checks passed", cp.stdout)

    def test_static_noncpp_backends_fail_closed_on_general_union_type_expr(self) -> None:
        east = _general_union_module()
        backends = [
            ("Rust backend", transpile_to_rust),
            ("C# backend", transpile_to_csharp),
            ("Go backend", transpile_to_go),
            ("Java backend", transpile_to_java),
            ("Kotlin backend", transpile_to_kotlin),
            ("Scala backend", transpile_to_scala),
            ("Swift backend", transpile_to_swift),
            ("Nim backend", transpile_to_nim),
        ]
        for backend_name, transpile in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "unsupported_syntax\\|" + re.escape(backend_name) + " does not support general union TypeExpr yet",
                ) as cm:
                    transpile(copy.deepcopy(east))
                self.assertIn("unsupported general-union lane: int64|bool", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
