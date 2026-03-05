#!/usr/bin/env python3
"""Generate runtime artifacts from a declarative manifest.

Source of truth is canonical Python modules under ``src/pytra``.
Per-target outputs and optional postprocess hooks are defined in
``tools/runtime_generation_manifest.json``.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from toolchain.compiler.backend_registry import emit_source, get_backend_spec, lower_ir, optimize_ir, resolve_layer_options
from toolchain.frontends.python_frontend import load_east3_document


DEFAULT_MANIFEST = ROOT / "tools" / "runtime_generation_manifest.json"
GENERATED_BY = "tools/gen_runtime_from_manifest.py"

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
    item_id: str
    source_rel: str
    target: str
    output_rel: str
    postprocess: str
    helper_name: str


def parse_csv_arg(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p != ""]


def _to_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def load_manifest_items(manifest_path: Path) -> list[GenerationItem]:
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    items_any = doc.get("items")
    if not isinstance(items_any, list):
        raise RuntimeError("manifest.items must be a list")
    out: list[GenerationItem] = []
    for item_obj in items_any:
        if not isinstance(item_obj, dict):
            continue
        item_id = _to_str(item_obj.get("id"))
        source_rel = _to_str(item_obj.get("source"))
        if item_id == "" or source_rel == "":
            raise RuntimeError("manifest item requires id/source")
        targets_any = item_obj.get("targets")
        if not isinstance(targets_any, list):
            raise RuntimeError("manifest item targets must be a list: " + item_id)
        for target_obj in targets_any:
            if not isinstance(target_obj, dict):
                continue
            target = _to_str(target_obj.get("target"))
            output_rel = _to_str(target_obj.get("output"))
            postprocess = _to_str(target_obj.get("postprocess"))
            helper_name = _to_str(target_obj.get("helper_name"))
            if target == "" or output_rel == "":
                raise RuntimeError("manifest target entry requires target/output: " + item_id)
            out.append(
                GenerationItem(
                    item_id=item_id,
                    source_rel=source_rel,
                    target=target,
                    output_rel=output_rel,
                    postprocess=postprocess,
                    helper_name=helper_name,
                )
            )
    return out


def resolve_targets(raw_targets: str, all_items: list[GenerationItem]) -> list[str]:
    known: list[str] = sorted({item.target for item in all_items})
    if raw_targets.strip() in {"", "all"}:
        return known
    targets = parse_csv_arg(raw_targets)
    unknown = [t for t in targets if t not in known]
    if len(unknown) > 0:
        raise RuntimeError("unknown targets: " + ", ".join(unknown))
    return targets


def resolve_item_ids(raw_items: str, all_items: list[GenerationItem]) -> list[str]:
    known: list[str] = sorted({item.item_id for item in all_items})
    if raw_items.strip() in {"", "all"}:
        return known
    ids = parse_csv_arg(raw_items)
    unknown = [x for x in ids if x not in known]
    if len(unknown) > 0:
        raise RuntimeError("unknown item id(s): " + ", ".join(unknown))
    return ids


def build_generation_plan(
    all_items: list[GenerationItem],
    targets: list[str],
    item_ids: list[str],
) -> list[GenerationItem]:
    target_set = set(targets)
    id_set = set(item_ids)
    out: list[GenerationItem] = []
    for item in all_items:
        if item.target not in target_set:
            continue
        if item.item_id not in id_set:
            continue
        out.append(item)
    return out


def run_py2x(target: str, source_rel: str, output_rel: str) -> str:
    src = ROOT / source_rel
    spec = get_backend_spec(target)
    target_lang = str(spec.get("target_lang", target))
    east_doc = load_east3_document(
        src,
        parser_backend="self_hosted",
        target_lang=target_lang,
    )
    lower_options = resolve_layer_options(spec, "lower", {})
    optimizer_options = resolve_layer_options(spec, "optimizer", {})
    emitter_options = resolve_layer_options(spec, "emitter", {})
    ir = lower_ir(spec, east_doc, lower_options)
    ir = optimize_ir(spec, ir, optimizer_options)
    out_name = Path(output_rel).name
    out_suffix = Path(output_rel).suffix
    if out_name == "":
        out_name = "tmp" + out_suffix
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / out_name
        out_text = emit_source(spec, ir, out, emitter_options)
        if out_text == "":
            return out.read_text(encoding="utf-8")
        return out_text


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
        prefix + " generated-by: " + GENERATED_BY,
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
    generated = run_py2x(item.target, item.source_rel, item.output_rel)
    if item.postprocess == "cs_program_to_helper":
        if item.helper_name == "":
            raise RuntimeError("missing helper_name for cs_program_to_helper: " + item.item_id)
        generated = rewrite_cs_program_to_helper(generated, item.helper_name)
    elif item.postprocess != "":
        raise RuntimeError("unknown postprocess: " + item.postprocess)
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
            print(item.target + ":" + item.item_id + " -> " + item.output_rel + (" [changed]" if changed else " [same]"))
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
    parser = argparse.ArgumentParser(description="generate runtime artifacts from declarative manifest")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="runtime manifest path")
    parser.add_argument("--targets", default="all", help="comma separated targets (default: all)")
    parser.add_argument("--items", default="all", help="comma separated item ids (default: all)")
    parser.add_argument("--check", action="store_true", help="fail when generated output differs")
    parser.add_argument("--dry-run", action="store_true", help="show plan and diff status without writing")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    all_items = load_manifest_items(manifest_path)
    targets = resolve_targets(args.targets, all_items)
    item_ids = resolve_item_ids(args.items, all_items)
    plan = build_generation_plan(all_items, targets, item_ids)
    checked, updated = generate(plan, check=bool(args.check), dry_run=bool(args.dry_run))
    print("summary: checked=" + str(checked) + " updated=" + str(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
