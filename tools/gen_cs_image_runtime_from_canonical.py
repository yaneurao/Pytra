#!/usr/bin/env python3
"""Generate C# image runtime helpers from canonical Python sources.

This script transpiles:
- src/pytra/utils/png.py
- src/pytra/utils/gif.py

and rewrites the generated `Program` class into runtime helpers:
- src/runtime/cs/pytra-gen/utils/png_helper.cs
- src/runtime/cs/pytra-gen/utils/gif_helper.cs
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_py2x(src_rel: str) -> str:
    src = ROOT / src_rel
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "tmp.cs"
        cp = subprocess.run(
            ["python3", "src/py2x.py", str(src), "--target", "cs", "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip() or f"exit={cp.returncode}"
            raise RuntimeError(f"py2x failed for {src_rel}: {msg}")
        return out.read_text(encoding="utf-8")


def _skip_main_method(body_lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        if line.strip().startswith("public static void Main("):
            brace_depth = 0
            while i < len(body_lines):
                cur = body_lines[i]
                brace_depth += cur.count("{")
                brace_depth -= cur.count("}")
                i += 1
                if brace_depth <= 0 and cur.strip() == "}":
                    break
            continue
        out.append(line)
        i += 1
    return out


def _rewrite_program_to_helper(cs_src: str, helper_name: str, source_rel: str) -> str:
    lines = cs_src.splitlines()

    using_lines: list[str] = []
    class_start = -1
    class_end = -1
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("using ") and line.strip() != "using Pytra.CsModule;":
            using_lines.append(line)
        if line.strip() == "public static class Program":
            class_start = i
            break
        i += 1
    if class_start < 0:
        raise RuntimeError("generated C# does not contain Program class")

    brace_depth = 0
    i = class_start
    seen_open = False
    while i < len(lines):
        cur = lines[i]
        if "{" in cur:
            seen_open = True
        brace_depth += cur.count("{")
        brace_depth -= cur.count("}")
        if seen_open and brace_depth == 0:
            class_end = i
            break
        i += 1
    if class_end < 0:
        raise RuntimeError("failed to locate end of Program class")

    body_lines = lines[class_start + 2 : class_end]
    body_lines = _skip_main_method(body_lines)

    out: list[str] = []
    out.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    out.append(f"// source: {source_rel}")
    out.append("// generated-by: tools/gen_cs_image_runtime_from_canonical.py")
    out.append("")
    out.extend(using_lines)
    if len(using_lines) > 0:
        out.append("")
    out.append("namespace Pytra.CsModule")
    out.append("{")
    out.append(f"    public static class {helper_name}")
    out.append("    {")
    for line in body_lines:
        if line.strip() == "":
            out.append("")
            continue
        out.append("    " + line)
    out.append("    }")
    out.append("}")
    out.append("")

    text = "\n".join(out)
    text = text.replace("Program.", f"{helper_name}.")
    return text


def generate() -> None:
    pairs = [
        ("src/pytra/utils/png.py", "png_helper", "src/runtime/cs/pytra-gen/utils/png_helper.cs"),
        ("src/pytra/utils/gif.py", "gif_helper", "src/runtime/cs/pytra-gen/utils/gif_helper.cs"),
    ]
    for src_rel, helper_name, out_rel in pairs:
        generated = _run_py2x(src_rel)
        rewritten = _rewrite_program_to_helper(generated, helper_name, src_rel)
        out_path = ROOT / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rewritten, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="generate C# image runtime helpers from canonical python sources")
    _ = parser.parse_args()
    generate()
    print("True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
