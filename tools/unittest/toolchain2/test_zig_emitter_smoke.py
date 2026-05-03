from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from toolchain.emit.zig.cli import _copy_zig_runtime
from toolchain.emit.zig.emitter import transpile_to_zig_native


class ZigEmitterSmokeTest(unittest.TestCase):
    def _work_root(self) -> Path:
        root = Path("work") / "tmp" / ("test_zig_emitter_smoke_" + uuid.uuid4().hex)
        root.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        return root

    def test_cli_runtime_copy_writes_root_entrypoint(self) -> None:
        out_dir = self._work_root()
        entry = out_dir / "toolchain" / "emit" / "cpp" / "cli.zig"
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("pub fn main() void {}\n", encoding="utf-8")
        _copy_zig_runtime(out_dir)
        main_path = out_dir / "main.zig"
        self.assertTrue(main_path.exists())
        self.assertIn('@import("toolchain/emit/cpp/cli.zig").main();', main_path.read_text(encoding="utf-8"))

    def test_import_bindings_emit_linked_user_symbol_import(self) -> None:
        east3 = {
            "kind": "Module",
            "east_stage": 3,
            "body": [],
            "meta": {
                "_cli_all_module_ids": ["toolchain.emit.common.cli_runner"],
                "import_bindings": [
                    {
                        "module_id": "toolchain.emit.common.cli_runner",
                        "runtime_module_id": "toolchain.emit.common.cli_runner",
                        "export_name": "run_emit_cli",
                        "local_name": "run_emit_cli",
                        "binding_kind": "symbol",
                    },
                    {
                        "module_id": "pytra.std.json",
                        "runtime_module_id": "pytra.std.json",
                        "export_name": "",
                        "local_name": "json",
                        "binding_kind": "module",
                        "resolved_binding_kind": "module",
                    },
                ],
            },
        }
        zig = transpile_to_zig_native(east3)

        self.assertIn('const json = @import("std/json.zig");', zig)
        self.assertIn('const toolchain_emit_common_cli_runner = @import("toolchain/emit/common/cli_runner.zig");', zig)
        self.assertIn("const run_emit_cli = toolchain_emit_common_cli_runner.run_emit_cli;", zig)

    def test_emit_tuple_unpack_stmt(self) -> None:
        east3 = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "pair",
                    "args": [],
                    "arg_types": {},
                    "return_type": "tuple[int64,int64]",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Tuple",
                                "elements": [
                                    {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                    {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                                ],
                                "resolved_type": "tuple[int64,int64]",
                            },
                        }
                    ],
                },
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [],
                    "arg_types": {},
                    "return_type": "int64",
                    "body": [
                        {
                            "kind": "TupleUnpack",
                            "declare": True,
                            "targets": [
                                {"kind": "Name", "id": "x", "resolved_type": "int64"},
                                {"kind": "Name", "id": "y", "resolved_type": "int64"},
                            ],
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "pair"},
                                "args": [],
                                "resolved_type": "tuple[int64,int64]",
                            },
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "BinOp",
                                "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                                "op": "Add",
                                "right": {"kind": "Name", "id": "y", "resolved_type": "int64"},
                                "resolved_type": "int64",
                            },
                        },
                    ],
                },
            ],
        }
        zig = transpile_to_zig_native(east3)

        self.assertIn("const __tmp_", zig)
        self.assertIn("const x = __tmp_", zig)
        self.assertIn("const y = __tmp_", zig)


if __name__ == "__main__":
    unittest.main()
