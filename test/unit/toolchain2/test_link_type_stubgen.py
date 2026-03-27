from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.parse.py.parse_python import parse_python_file
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2
from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.optimize.optimizer import optimize_east3_document
from toolchain2.link.linker import link_modules
from toolchain2.link.type_stubgen import (
    available_type_stub_module_ids,
    build_type_stub_doc,
    write_type_stub_files,
)


def _build_current_selfhost_east3_paths(tmpdir: Path) -> list[str]:
    inputs: list[Path] = []
    for p in sorted((ROOT / "test" / "selfhost" / "east3-opt").rglob("*.east3")):
        data = json.loads(p.read_text(encoding="utf-8"))
        source_path = data.get("source_path", "")
        if isinstance(source_path, str) and source_path.startswith("src/toolchain2/"):
            inputs.append(ROOT / source_path)
    inputs = sorted(dict.fromkeys(inputs))

    builtins_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1"
    containers_path = ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1"
    stdlib_dir = ROOT / "test" / "include" / "east1" / "py" / "std"
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)

    outdir = tmpdir / "selfhost-e3"
    shutil.rmtree(outdir, ignore_errors=True)
    outdir.mkdir(parents=True, exist_ok=True)

    out_paths: list[str] = []
    for src in inputs:
        rel = str(src.relative_to(ROOT)).replace("\\", "/")
        east1 = parse_python_file(str(src))
        east1["source_path"] = rel
        resolve_east1_to_east2(east1, registry=registry)
        east3 = lower_east2_to_east3(east1)
        east3["source_path"] = rel
        east3, _ = optimize_east3_document(east3, opt_level=1)
        east3["source_path"] = rel
        target = outdir / (rel.replace("/", "__").replace(".py", "") + ".east3")
        target.write_text(json.dumps(east3, ensure_ascii=False), encoding="utf-8")
        out_paths.append(str(target))
    return out_paths


class Toolchain2LinkTypeStubgenTests(unittest.TestCase):
    def test_type_stub_registry_covers_current_selfhost_missing_modules(self) -> None:
        available = set(available_type_stub_module_ids())

        self.assertIn("toolchain2.compile.jv", available)
        self.assertIn("toolchain2.link.expand_defaults", available)
        self.assertIn("toolchain2.optimize.passes", available)
        self.assertIn("toolchain2.parse.py.nodes", available)
        self.assertIn("toolchain2.parse.py.parser", available)
        self.assertIn("toolchain2.resolve.py.builtin_registry", available)
        self.assertIn("toolchain2.resolve.py.normalize_order", available)

    def test_build_type_stub_doc_exposes_key_declarations(self) -> None:
        compile_jv = build_type_stub_doc("toolchain2.compile.jv")
        names = {
            node.get("name")
            for node in compile_jv["body"]
            if isinstance(node, dict) and isinstance(node.get("name"), str)
        }
        self.assertIn("CompileContext", names)
        self.assertIn("nd_kind", names)

        registry_doc = build_type_stub_doc("toolchain2.resolve.py.builtin_registry")
        reg_names = {
            node.get("name")
            for node in registry_doc["body"]
            if isinstance(node, dict) and isinstance(node.get("name"), str)
        }
        self.assertIn("BuiltinRegistry", reg_names)
        self.assertIn("load_builtin_registry", reg_names)

    def test_selfhost_link_succeeds_when_missing_modules_are_stubbed(self) -> None:
        missing_modules = [
            "toolchain2.compile.jv",
            "toolchain2.link.expand_defaults",
            "toolchain2.optimize.passes",
            "toolchain2.parse.py.nodes",
            "toolchain2.parse.py.parser",
            "toolchain2.resolve.py.builtin_registry",
            "toolchain2.resolve.py.normalize_order",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            paths = _build_current_selfhost_east3_paths(tmpdir)
            stub_paths = write_type_stub_files(missing_modules, tmpdir / "stubs")

            result = link_modules(paths + stub_paths, target="go", dispatch_mode="native")

        module_ids = {module.module_id for module in result.linked_modules}
        for module_id in missing_modules:
            self.assertIn(module_id, module_ids)


if __name__ == "__main__":
    unittest.main()
