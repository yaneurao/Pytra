"""C++ backend CLI: manifest.json → C++ multi-file output."""
from __future__ import annotations

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.cpp.runtime_bundle import write_helper_module_artifacts
from toolchain.emit.cpp.runtime_bundle import write_runtime_module_artifacts
from toolchain.emit.cpp.runtime_bundle import write_user_module_artifacts


def _helper_cpp_rel_path(module_id: str) -> str:
    if module_id.startswith("pytra."):
        return module_id[len("pytra."):].replace(".", "/")
    return module_id.replace(".", "/")


def _emit_cpp_direct(east_doc: dict[str, JsonVal], output_dir: Path) -> int:
    """Emit C++ files directly. Handles module_kind branching internally."""
    meta: JsonVal = east_doc.get("meta")
    module_id: str = ""
    module_kind: str = ""
    source_path: str = ""
    meta_obj = json.JsonValue(meta).as_obj()
    if meta_obj is not None:
        mid = json.JsonValue(meta_obj.raw.get("_cli_module_id")).as_str()
        if mid is not None:
            module_id = mid
        mk = json.JsonValue(meta_obj.raw.get("_cli_module_kind")).as_str()
        if mk is not None:
            module_kind = mk
        sp = json.JsonValue(meta_obj.raw.get("_cli_source_path")).as_str()
        if sp is not None:
            source_path = sp
    if module_kind == "runtime":
        return write_runtime_module_artifacts(
            module_id,
            east_doc,
            output_dir=output_dir,
            source_path=source_path,
        )
    if module_kind == "helper":
        rel_header_path: str = _helper_cpp_rel_path(module_id) + ".h"
        return write_helper_module_artifacts(
            module_id,
            east_doc,
            output_dir=output_dir,
            rel_header_path=rel_header_path,
        )
    return write_user_module_artifacts(
        module_id,
        east_doc,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    import sys
    cli_argv: list[str] | None = sys.argv[1:]
    exit_code: int = run_emit_cli(None, cli_argv, "", None, _emit_cpp_direct)
    if exit_code != 0:
        raise RuntimeError("emit failed")
