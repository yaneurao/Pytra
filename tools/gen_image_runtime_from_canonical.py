#!/usr/bin/env python3
"""Generate image runtime artifacts from canonical Python sources.

Source of truth:
- src/pytra/utils/png.py
- src/pytra/utils/gif.py

This tool defines a shared output convention for all targets:
- src/runtime/<lang>/pytra-gen/...
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_MODULES: dict[str, str] = {
    "png": "src/pytra/utils/png.py",
    "gif": "src/pytra/utils/gif.py",
}

TARGET_OUTPUTS: dict[str, dict[str, str]] = {
    "cpp": {
        "png": "src/runtime/cpp/pytra-gen/utils/png.cpp",
        "gif": "src/runtime/cpp/pytra-gen/utils/gif.cpp",
    },
    "rs": {
        "png": "src/runtime/rs/pytra-gen/utils/png.rs",
        "gif": "src/runtime/rs/pytra-gen/utils/gif.rs",
    },
    "cs": {
        "png": "src/runtime/cs/pytra-gen/utils/png_helper.cs",
        "gif": "src/runtime/cs/pytra-gen/utils/gif_helper.cs",
    },
    "js": {
        "png": "src/runtime/js/pytra-gen/utils/png_helper.js",
        "gif": "src/runtime/js/pytra-gen/utils/gif_helper.js",
    },
    "ts": {
        "png": "src/runtime/ts/pytra-gen/utils/png_helper.ts",
        "gif": "src/runtime/ts/pytra-gen/utils/gif_helper.ts",
    },
    "go": {
        "png": "src/runtime/go/pytra-gen/utils/png.go",
        "gif": "src/runtime/go/pytra-gen/utils/gif.go",
    },
    "java": {
        "png": "src/runtime/java/pytra-gen/utils/PngHelper.java",
        "gif": "src/runtime/java/pytra-gen/utils/GifHelper.java",
    },
    "swift": {
        "png": "src/runtime/swift/pytra-gen/utils/png_helper.swift",
        "gif": "src/runtime/swift/pytra-gen/utils/gif_helper.swift",
    },
    "kotlin": {
        "png": "src/runtime/kotlin/pytra-gen/utils/png_helper.kt",
        "gif": "src/runtime/kotlin/pytra-gen/utils/gif_helper.kt",
    },
    "ruby": {
        "png": "src/runtime/ruby/pytra-gen/utils/png_helper.rb",
        "gif": "src/runtime/ruby/pytra-gen/utils/gif_helper.rb",
    },
    "lua": {
        "png": "src/runtime/lua/pytra-gen/utils/png_helper.lua",
        "gif": "src/runtime/lua/pytra-gen/utils/gif_helper.lua",
    },
    "scala": {
        "png": "src/runtime/scala/pytra-gen/utils/png_helper.scala",
        "gif": "src/runtime/scala/pytra-gen/utils/gif_helper.scala",
    },
    "php": {
        "png": "src/runtime/php/pytra-gen/runtime/png.php",
        "gif": "src/runtime/php/pytra-gen/runtime/gif.php",
    },
    "nim": {
        "png": "src/runtime/nim/pytra-gen/utils/png_helper.nim",
        "gif": "src/runtime/nim/pytra-gen/utils/gif_helper.nim",
    },
}

CS_HELPER_NAMES = {"png": "png_helper", "gif": "gif_helper"}

COMMENT_PREFIX: dict[str, str] = {
    "cpp": "//",
    "rs": "//",
    "cs": "//",
    "js": "//",
    "ts": "//",
    "go": "//",
    "java": "//",
    "swift": "//",
    "kotlin": "//",
    "ruby": "#",
    "lua": "--",
    "scala": "//",
    "php": "//",
    "nim": "#",
}


@dataclass(frozen=True)
class GenerationItem:
    target: str
    module: str
    source_rel: str
    output_rel: str


def parse_csv_arg(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p != ""]


def resolve_targets(raw_targets: str) -> list[str]:
    if raw_targets.strip() in {"", "all"}:
        return list(TARGET_OUTPUTS.keys())
    targets = parse_csv_arg(raw_targets)
    unknown = [t for t in targets if t not in TARGET_OUTPUTS]
    if len(unknown) > 0:
        raise RuntimeError("unknown targets: " + ", ".join(unknown))
    return targets


def resolve_modules(raw_modules: str) -> list[str]:
    modules = parse_csv_arg(raw_modules)
    if len(modules) == 0:
        modules = ["png", "gif"]
    unknown = [m for m in modules if m not in CANONICAL_MODULES]
    if len(unknown) > 0:
        raise RuntimeError("unknown modules: " + ", ".join(unknown))
    return modules


def build_generation_plan(targets: list[str], modules: list[str]) -> list[GenerationItem]:
    out: list[GenerationItem] = []
    for target in targets:
        target_map = TARGET_OUTPUTS.get(target, {})
        for module in modules:
            output_rel = target_map.get(module)
            if not isinstance(output_rel, str):
                raise RuntimeError("missing output path map: " + target + ":" + module)
            out.append(
                GenerationItem(
                    target=target,
                    module=module,
                    source_rel=CANONICAL_MODULES[module],
                    output_rel=output_rel,
                )
            )
    return out


def run_py2x(target: str, source_rel: str, ext_hint: str) -> str:
    src = ROOT / source_rel
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / ("tmp" + ext_hint)
        cp = subprocess.run(
            ["python3", "src/py2x.py", str(src), "--target", target, "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip() or ("exit=" + str(cp.returncode))
            raise RuntimeError("py2x failed [" + target + ":" + source_rel + "]: " + msg)
        return out.read_text(encoding="utf-8")


def _skip_cs_main_method(body_lines: list[str]) -> list[str]:
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


def rewrite_cs_program_to_helper(cs_src: str, helper_name: str) -> str:
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
    body_lines = _skip_cs_main_method(body_lines)
    out: list[str] = []
    out.extend(using_lines)
    if len(using_lines) > 0:
        out.append("")
    out.append("namespace Pytra.CsModule")
    out.append("{")
    out.append("    public static class " + helper_name)
    out.append("    {")
    for line in body_lines:
        if line.strip() == "":
            out.append("")
        else:
            out.append("    " + line)
    out.append("    }")
    out.append("}")
    out.append("")
    text = "\n".join(out)
    return text.replace("Program.", helper_name + ".")


def inject_generated_header(text: str, target: str, source_rel: str) -> str:
    prefix = COMMENT_PREFIX.get(target)
    if prefix is None:
        raise RuntimeError("missing comment prefix for target: " + target)

    header_lines = [
        prefix + " AUTO-GENERATED FILE. DO NOT EDIT.",
        prefix + " source: " + source_rel,
        prefix + " generated-by: tools/gen_image_runtime_from_canonical.py",
    ]
    header_blob = "\n".join(header_lines)

    if target == "php" and text.startswith("<?php"):
        parts = text.splitlines()
        first = parts[0]
        rest = parts[1:]
        return first + "\n" + header_blob + "\n\n" + "\n".join(rest) + ("\n" if text.endswith("\n") else "")

    suffix = "\n" if text.endswith("\n") else ""
    body = text.rstrip("\n")
    return header_blob + "\n\n" + body + suffix


def render_item(item: GenerationItem) -> str:
    ext_hint = Path(item.output_rel).suffix
    generated = run_py2x(item.target, item.source_rel, ext_hint)
    if item.target == "cs":
        helper_name = CS_HELPER_NAMES.get(item.module)
        if helper_name is None:
            raise RuntimeError("missing C# helper map for module: " + item.module)
        generated = rewrite_cs_program_to_helper(generated, helper_name)
    return inject_generated_header(generated, item.target, item.source_rel)


def generate(plan: list[GenerationItem], *, check: bool, dry_run: bool) -> tuple[int, int]:
    updated = 0
    checked = 0
    for item in plan:
        out_path = ROOT / item.output_rel
        rendered = render_item(item)
        current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        changed = (current != rendered)
        checked += 1
        if dry_run:
            print(item.target + ":" + item.module + " -> " + item.output_rel + (" [changed]" if changed else " [same]"))
            continue
        if check:
            if changed:
                raise RuntimeError("stale generated runtime: " + item.output_rel)
            continue
        if changed:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            updated += 1
            print("updated: " + item.output_rel)
        else:
            print("unchanged: " + item.output_rel)
    return checked, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="generate image runtime artifacts from canonical python sources")
    parser.add_argument("--targets", default="all", help="comma separated targets (default: all)")
    parser.add_argument("--modules", default="png,gif", help="comma separated modules (png,gif)")
    parser.add_argument("--check", action="store_true", help="fail when generated output differs")
    parser.add_argument("--dry-run", action="store_true", help="show plan and diff status without writing")
    args = parser.parse_args()

    targets = resolve_targets(args.targets)
    modules = resolve_modules(args.modules)
    plan = build_generation_plan(targets, modules)
    checked, updated = generate(plan, check=args.check, dry_run=args.dry_run)
    print("summary: checked=" + str(checked) + " updated=" + str(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
