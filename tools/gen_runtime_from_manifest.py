#!/usr/bin/env python3
"""Generate runtime artifacts from a declarative manifest.

Source of truth is canonical Python modules under ``src/pytra``.
Per-target outputs and optional postprocess hooks are defined in
``tools/runtime_generation_manifest.json``.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from toolchain.compiler.backend_registry_static import (
    emit_source,
    get_backend_spec,
    lower_ir,
    optimize_ir,
    resolve_layer_options,
)
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
            if out.exists():
                return out.read_text(encoding="utf-8")
            raise RuntimeError(
                "runtime generation backend emitted no inline text and wrote no file: "
                + target
                + " -> "
                + output_rel
            )
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


def rewrite_cs_std_time_live_wrapper(cs_src: str) -> str:
    text = rewrite_cs_program_to_helper(cs_src, "time")
    return text.replace("return __t.perf_counter();", "return time_native.perf_counter();")


def rewrite_java_std_time_live_wrapper(java_src: str) -> str:
    return java_src.replace(
        "return __t.perf_counter();",
        "return (double) System.nanoTime() / 1_000_000_000.0;",
    )


def rewrite_java_std_math_live_wrapper(java_src: str) -> str:
    text = java_src
    text = text.replace("public static double pi = extern(math.pi);", "public static double pi = Math.PI;")
    text = text.replace("public static double e = extern(math.e);", "public static double e = Math.E;")
    replacements = {
        "return math.sqrt(x);": "return Math.sqrt(x);",
        "return math.sin(x);": "return Math.sin(x);",
        "return math.cos(x);": "return Math.cos(x);",
        "return math.tan(x);": "return Math.tan(x);",
        "return math.exp(x);": "return Math.exp(x);",
        "return math.log(x);": "return Math.log(x);",
        "return math.log10(x);": "return Math.log10(x);",
        "return math.fabs(x);": "return Math.abs(x);",
        "return math.floor(x);": "return Math.floor(x);",
        "return math.ceil(x);": "return Math.ceil(x);",
        "return math.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return text


def rewrite_js_std_math_live_wrapper(js_src: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    text = text.replace('import { extern } from "./pytra/std.js";\n\n', "")
    text = text.replace('"pytra.std.math: extern-marked math API with Python runtime fallback.";\n', "")
    text = text.replace("let pi = extern(__m.pi);", "const pi = Math.PI;")
    text = text.replace("let e = extern(__m.e);", "const e = Math.E;")
    replacements = {
        "return __m.sqrt(x);": "return Math.sqrt(x);",
        "return __m.sin(x);": "return Math.sin(x);",
        "return __m.cos(x);": "return Math.cos(x);",
        "return __m.tan(x);": "return Math.tan(x);",
        "return __m.exp(x);": "return Math.exp(x);",
        "return __m.log(x);": "return Math.log(x);",
        "return __m.log10(x);": "return Math.log10(x);",
        "return __m.fabs(x);": "return Math.abs(x);",
        "return __m.floor(x);": "return Math.floor(x);",
        "return __m.ceil(x);": "return Math.ceil(x);",
        "return __m.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "extern(" in text or "__m." in text:
        raise RuntimeError("generated JS std/math wrapper still contains extern/math runtime residue")
    return text.rstrip() + "\n\nmodule.exports = { pi, e, sin, cos, tan, sqrt, exp, log, log10, fabs, floor, ceil, pow };\n"


def _strip_trailing_string_literal_expr(text: str) -> str:
    lines = text.splitlines()
    if len(lines) == 0:
        return text
    literal_re = re.compile(r"""^\s*(["']).*\1;\s*$""")
    while len(lines) > 0 and literal_re.match(lines[-1]):
        lines.pop()
    if len(lines) == 0:
        return ""
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _remove_block_by_signature(lines: list[str], signature_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if signature_re.match(line.strip()):
            brace_depth = 0
            seen_open = False
            while i < len(lines):
                cur = lines[i]
                if "{" in cur:
                    seen_open = True
                brace_depth += cur.count("{")
                brace_depth -= cur.count("}")
                i += 1
                if seen_open and brace_depth <= 0:
                    break
            continue
        out.append(line)
        i += 1
    return out


def rewrite_js_program_to_cjs_module(js_src: str) -> str:
    js_src = _strip_trailing_string_literal_expr(js_src)
    js_src = re.sub(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\.extend\(([^;\n]+)\);",
        r"\1 = \1.concat(\2);",
        js_src,
    )
    js_src = re.sub(r"(?<!>)>>(?!>)", ">>>", js_src)

    if "module.exports" in js_src:
        return js_src
    names: list[str] = []
    for m in re.finditer(r"(?m)^function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", js_src):
        name = m.group(1)
        if name not in names:
            names.append(name)
    public_names = [name for name in names if not name.startswith("_")]
    if len(public_names) == 0:
        return js_src
    body = js_src.rstrip("\n")
    if "open(" in body and "function open(" not in body:
        prelude = (
            "const fs = require('node:fs');\n"
            "const path = require('node:path');\n"
            "function open(pathLike, mode) {\n"
            "    const filePath = String(pathLike);\n"
            "    const writeMode = String(mode || 'wb');\n"
            "    return {\n"
            "        write(data) {\n"
            "            const bytes = Array.isArray(data) ? data : Array.from(data || []);\n"
            "            fs.mkdirSync(path.dirname(filePath), { recursive: true });\n"
            "            const flag = (writeMode === 'ab' || writeMode === 'a') ? 'a' : 'w';\n"
            "            fs.writeFileSync(filePath, Buffer.from(bytes), { flag });\n"
            "        },\n"
            "        close() {},\n"
            "    };\n"
            "}\n\n"
        )
        body = prelude + body
    exports = "module.exports = {" + ", ".join(public_names) + "};\n"
    return body + "\n\n" + exports


def rewrite_js_std_time_live_wrapper(js_src: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    text = text.replace(
        "return __t.perf_counter();",
        "return Number(process.hrtime.bigint()) / 1_000_000_000;",
    ).rstrip()
    if "function perf_counter(" not in text:
        raise RuntimeError("generated JS std/time wrapper is missing perf_counter()")
    return text + "\n\nconst perfCounter = perf_counter;\nmodule.exports = {perf_counter, perfCounter};\n"


def rewrite_js_std_pathlib_live_wrapper(js_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__(rhs)",
        "parent()",
        "parents()",
        "name()",
        "suffix()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(parents, exist_ok)",
        "read_text(encoding)",
        "write_text(text, encoding)",
        "glob(pattern)",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in js_src:
            raise RuntimeError("generated JS std/pathlib wrapper is missing: " + fragment)
    return (
        'const fs = require("fs");\n'
        'const nodepath = require("path");\n\n'
        "function _coercePathText(value) {\n"
        "    if (value && typeof value.__fspath__ === \"function\") {\n"
        "        return String(value.__fspath__());\n"
        "    }\n"
        "    if (value && typeof value.toString === \"function\" && value.toString !== Object.prototype.toString) {\n"
        "        return String(value.toString());\n"
        "    }\n"
        "    return String(value ?? \"\");\n"
        "}\n\n"
        "function _globSegmentToRegExp(segment) {\n"
        "    const escaped = String(segment).replace(/[|\\\\{}()[\\]^$+?.]/g, \"\\\\$&\");\n"
        "    return new RegExp(\"^\" + escaped.replace(/\\*/g, \".*\") + \"$\");\n"
        "}\n\n"
        "function _globPaths(pattern) {\n"
        "    const text = _coercePathText(pattern);\n"
        "    if (text.indexOf(\"*\") === -1) {\n"
        "        return fs.existsSync(text) ? [text] : [];\n"
        "    }\n"
        "    const normalized = text.replace(/\\\\/g, \"/\");\n"
        "    const lastSlash = normalized.lastIndexOf(\"/\");\n"
        "    const baseDir = lastSlash >= 0 ? normalized.slice(0, lastSlash) : \".\";\n"
        "    const leafPattern = lastSlash >= 0 ? normalized.slice(lastSlash + 1) : normalized;\n"
        "    const dirPath = baseDir === \"\" ? \".\" : baseDir;\n"
        "    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {\n"
        "        return [];\n"
        "    }\n"
        "    const leafRe = _globSegmentToRegExp(leafPattern);\n"
        "    const out = [];\n"
        "    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {\n"
        "        if (!leafRe.test(entry.name)) {\n"
        "            continue;\n"
        "        }\n"
        "        out.push(nodepath.join(dirPath, entry.name));\n"
        "    }\n"
        "    return out;\n"
        "}\n\n"
        "class PathValue {\n"
        "    constructor(value) {\n"
        "        this._value = _coercePathText(value);\n"
        "    }\n\n"
        "    __str__() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __repr__() {\n"
        "        return \"Path(\" + this._value + \")\";\n"
        "    }\n\n"
        "    __fspath__() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __truediv__(rhs) {\n"
        "        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));\n"
        "    }\n\n"
        "    parent() {\n"
        "        let parentTxt = nodepath.dirname(this._value);\n"
        "        if (parentTxt === \"\") {\n"
        "            parentTxt = \".\";\n"
        "        }\n"
        "        return new PathValue(parentTxt);\n"
        "    }\n\n"
        "    parents() {\n"
        "        const out = [];\n"
        "        let current = nodepath.dirname(this._value);\n"
        "        while (true) {\n"
        "            if (current === \"\") {\n"
        "                current = \".\";\n"
        "            }\n"
        "            out.push(new PathValue(current));\n"
        "            let nextCurrent = nodepath.dirname(current);\n"
        "            if (nextCurrent === \"\") {\n"
        "                nextCurrent = \".\";\n"
        "            }\n"
        "            if (nextCurrent === current) {\n"
        "                break;\n"
        "            }\n"
        "            current = nextCurrent;\n"
        "        }\n"
        "        return out;\n"
        "    }\n\n"
        "    name() {\n"
        "        return nodepath.basename(this._value);\n"
        "    }\n\n"
        "    suffix() {\n"
        "        return nodepath.extname(this._value);\n"
        "    }\n\n"
        "    stem() {\n"
        "        return nodepath.parse(this._value).name;\n"
        "    }\n\n"
        "    resolve() {\n"
        "        return new PathValue(nodepath.resolve(this._value));\n"
        "    }\n\n"
        "    exists() {\n"
        "        return fs.existsSync(this._value);\n"
        "    }\n\n"
        "    mkdir(parents = false, exist_ok = false) {\n"
        "        if (parents) {\n"
        "            fs.mkdirSync(this._value, { recursive: true });\n"
        "            return;\n"
        "        }\n"
        "        try {\n"
        "            fs.mkdirSync(this._value);\n"
        "        } catch (err) {\n"
        "            if (!(exist_ok && err && err.code === \"EEXIST\")) {\n"
        "                throw err;\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    read_text(_encoding = \"utf-8\") {\n"
        "        return fs.readFileSync(this._value, \"utf8\");\n"
        "    }\n\n"
        "    write_text(text, _encoding = \"utf-8\") {\n"
        "        const rendered = String(text);\n"
        "        fs.writeFileSync(this._value, rendered, \"utf8\");\n"
        "        return rendered.length;\n"
        "    }\n\n"
        "    glob(pattern) {\n"
        "        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));\n"
        "        return matches.map((item) => new PathValue(item));\n"
        "    }\n\n"
        "    toString() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    static cwd() {\n"
        "        return new PathValue(process.cwd());\n"
        "    }\n"
        "}\n\n"
        "function _wrap_path_obj(obj) {\n"
        "    if (!(obj instanceof PathValue)) {\n"
        "        return obj;\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parent\")) {\n"
        "        Object.defineProperty(obj, \"parent\", { get: function() { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parents\")) {\n"
        "        Object.defineProperty(obj, \"parents\", { get: function() { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"name\")) {\n"
        "        Object.defineProperty(obj, \"name\", { get: function() { return PathValue.prototype.name.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"suffix\")) {\n"
        "        Object.defineProperty(obj, \"suffix\", { get: function() { return PathValue.prototype.suffix.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"stem\")) {\n"
        "        Object.defineProperty(obj, \"stem\", { get: function() { return PathValue.prototype.stem.call(this); }, configurable: true });\n"
        "    }\n"
        "    return obj;\n"
        "}\n\n"
        "function Path(value = \"\") {\n"
        "    return _wrap_path_obj(new PathValue(value));\n"
        "}\n\n"
        "Path.cwd = function() {\n"
        "    return _wrap_path_obj(PathValue.cwd());\n"
        "};\n\n"
        "function pathJoin(base, child) {\n"
        "    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));\n"
        "}\n\n"
        "module.exports = { Path, pathJoin };\n"
    )


def rewrite_ts_std_math_live_wrapper(ts_src: str) -> str:
    text = _strip_trailing_string_literal_expr(ts_src)
    text = text.replace('import { extern } from "./pytra/std.js";\n\n', "")
    text = text.replace('"pytra.std.math: extern-marked math API with Python runtime fallback.";\n', "")
    text = text.replace("let pi = extern(__m.pi);", "export const pi: number = Math.PI;")
    text = text.replace("let e = extern(__m.e);", "export const e: number = Math.E;")
    signature_replacements = {
        "function sqrt(x) {": "export function sqrt(x: number): number {",
        "function sin(x) {": "export function sin(x: number): number {",
        "function cos(x) {": "export function cos(x: number): number {",
        "function tan(x) {": "export function tan(x: number): number {",
        "function exp(x) {": "export function exp(x: number): number {",
        "function log(x) {": "export function log(x: number): number {",
        "function log10(x) {": "export function log10(x: number): number {",
        "function fabs(x) {": "export function fabs(x: number): number {",
        "function floor(x) {": "export function floor(x: number): number {",
        "function ceil(x) {": "export function ceil(x: number): number {",
        "function pow(x, y) {": "export function pow(x: number, y: number): number {",
    }
    for before, after in signature_replacements.items():
        text = text.replace(before, after)
    replacements = {
        "return __m.sqrt(x);": "return Math.sqrt(x);",
        "return __m.sin(x);": "return Math.sin(x);",
        "return __m.cos(x);": "return Math.cos(x);",
        "return __m.tan(x);": "return Math.tan(x);",
        "return __m.exp(x);": "return Math.exp(x);",
        "return __m.log(x);": "return Math.log(x);",
        "return __m.log10(x);": "return Math.log10(x);",
        "return __m.fabs(x);": "return Math.abs(x);",
        "return __m.floor(x);": "return Math.floor(x);",
        "return __m.ceil(x);": "return Math.ceil(x);",
        "return __m.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "extern(" in text or "__m." in text:
        raise RuntimeError("generated TS std/math wrapper still contains extern/math runtime residue")
    return text.rstrip() + "\n"


def rewrite_ts_std_time_live_wrapper(ts_src: str) -> str:
    text = _strip_trailing_string_literal_expr(ts_src)
    text = text.replace(
        "function perf_counter() {",
        "export function perf_counter(): number {",
        1,
    )
    text = text.replace(
        "return __t.perf_counter();",
        "return Number(process.hrtime.bigint()) / 1_000_000_000;",
    ).rstrip()
    if "export function perf_counter(): number {" not in text:
        raise RuntimeError("generated TS std/time wrapper is missing perf_counter()")
    return text + "\n\nexport const perfCounter = perf_counter;\n"


def rewrite_ts_std_pathlib_live_wrapper(ts_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__(rhs)",
        "parent()",
        "parents()",
        "name()",
        "suffix()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(parents, exist_ok)",
        "read_text(encoding)",
        "write_text(text, encoding)",
        "glob(pattern)",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in ts_src:
            raise RuntimeError("generated TS std/pathlib wrapper is missing: " + fragment)
    return (
        'import * as fs from "fs";\n'
        'import * as nodepath from "path";\n\n'
        "function _coercePathText(value: unknown): string {\n"
        "    const maybePath = value as { __fspath__?: () => unknown; toString?: () => string } | null | undefined;\n"
        "    if (maybePath && typeof maybePath.__fspath__ === \"function\") {\n"
        "        return String(maybePath.__fspath__());\n"
        "    }\n"
        "    if (maybePath && typeof maybePath.toString === \"function\" && maybePath.toString !== Object.prototype.toString) {\n"
        "        return String(maybePath.toString());\n"
        "    }\n"
        "    return String(value ?? \"\");\n"
        "}\n\n"
        "function _globSegmentToRegExp(segment: string): RegExp {\n"
        "    const escaped = String(segment).replace(/[|\\\\{}()[\\]^$+?.]/g, \"\\\\$&\");\n"
        "    return new RegExp(\"^\" + escaped.replace(/\\*/g, \".*\") + \"$\");\n"
        "}\n\n"
        "function _globPaths(pattern: string): string[] {\n"
        "    const text = _coercePathText(pattern);\n"
        "    if (text.indexOf(\"*\") === -1) {\n"
        "        return fs.existsSync(text) ? [text] : [];\n"
        "    }\n"
        "    const normalized = text.replace(/\\\\/g, \"/\");\n"
        "    const lastSlash = normalized.lastIndexOf(\"/\");\n"
        "    const baseDir = lastSlash >= 0 ? normalized.slice(0, lastSlash) : \".\";\n"
        "    const leafPattern = lastSlash >= 0 ? normalized.slice(lastSlash + 1) : normalized;\n"
        "    const dirPath = baseDir === \"\" ? \".\" : baseDir;\n"
        "    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {\n"
        "        return [];\n"
        "    }\n"
        "    const leafRe = _globSegmentToRegExp(leafPattern);\n"
        "    const out: string[] = [];\n"
        "    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {\n"
        "        if (!leafRe.test(entry.name)) {\n"
        "            continue;\n"
        "        }\n"
        "        out.push(nodepath.join(dirPath, entry.name));\n"
        "    }\n"
        "    return out;\n"
        "}\n\n"
        "export class PathValue {\n"
        "    _value: string;\n\n"
        "    constructor(value: unknown) {\n"
        "        this._value = _coercePathText(value);\n"
        "    }\n\n"
        "    __str__(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __repr__(): string {\n"
        "        return \"Path(\" + this._value + \")\";\n"
        "    }\n\n"
        "    __fspath__(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __truediv__(rhs: unknown): PathValue {\n"
        "        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));\n"
        "    }\n\n"
        "    parent(): PathValue {\n"
        "        let parentTxt = nodepath.dirname(this._value);\n"
        "        if (parentTxt === \"\") {\n"
        "            parentTxt = \".\";\n"
        "        }\n"
        "        return new PathValue(parentTxt);\n"
        "    }\n\n"
        "    parents(): PathValue[] {\n"
        "        const out: PathValue[] = [];\n"
        "        let current = nodepath.dirname(this._value);\n"
        "        while (true) {\n"
        "            if (current === \"\") {\n"
        "                current = \".\";\n"
        "            }\n"
        "            out.push(new PathValue(current));\n"
        "            let nextCurrent = nodepath.dirname(current);\n"
        "            if (nextCurrent === \"\") {\n"
        "                nextCurrent = \".\";\n"
        "            }\n"
        "            if (nextCurrent === current) {\n"
        "                break;\n"
        "            }\n"
        "            current = nextCurrent;\n"
        "        }\n"
        "        return out;\n"
        "    }\n\n"
        "    name(): string {\n"
        "        return nodepath.basename(this._value);\n"
        "    }\n\n"
        "    suffix(): string {\n"
        "        return nodepath.extname(this._value);\n"
        "    }\n\n"
        "    stem(): string {\n"
        "        return nodepath.parse(this._value).name;\n"
        "    }\n\n"
        "    resolve(): PathValue {\n"
        "        return new PathValue(nodepath.resolve(this._value));\n"
        "    }\n\n"
        "    exists(): boolean {\n"
        "        return fs.existsSync(this._value);\n"
        "    }\n\n"
        "    mkdir(parents: boolean = false, exist_ok: boolean = false): void {\n"
        "        if (parents) {\n"
        "            fs.mkdirSync(this._value, { recursive: true });\n"
        "            return;\n"
        "        }\n"
        "        try {\n"
        "            fs.mkdirSync(this._value);\n"
        "        } catch (err: unknown) {\n"
        "            const e = err as { code?: string };\n"
        "            if (!(exist_ok && e.code === \"EEXIST\")) {\n"
        "                throw err;\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    read_text(_encoding: string = \"utf-8\"): string {\n"
        "        return fs.readFileSync(this._value, \"utf8\");\n"
        "    }\n\n"
        "    write_text(text: unknown, _encoding: string = \"utf-8\"): number {\n"
        "        const rendered = String(text);\n"
        "        fs.writeFileSync(this._value, rendered, \"utf8\");\n"
        "        return rendered.length;\n"
        "    }\n\n"
        "    glob(pattern: string): PathValue[] {\n"
        "        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));\n"
        "        return matches.map((item) => new PathValue(item));\n"
        "    }\n\n"
        "    toString(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    static cwd(): PathValue {\n"
        "        return new PathValue(process.cwd());\n"
        "    }\n"
        "}\n\n"
        "function _wrap_path_obj(obj: PathValue): PathValue {\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parent\")) {\n"
        "        Object.defineProperty(obj, \"parent\", { get: function(this: PathValue) { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parents\")) {\n"
        "        Object.defineProperty(obj, \"parents\", { get: function(this: PathValue) { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"name\")) {\n"
        "        Object.defineProperty(obj, \"name\", { get: function(this: PathValue) { return PathValue.prototype.name.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"suffix\")) {\n"
        "        Object.defineProperty(obj, \"suffix\", { get: function(this: PathValue) { return PathValue.prototype.suffix.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"stem\")) {\n"
        "        Object.defineProperty(obj, \"stem\", { get: function(this: PathValue) { return PathValue.prototype.stem.call(this); }, configurable: true });\n"
        "    }\n"
        "    return obj;\n"
        "}\n\n"
        "export const Path: ((value?: unknown) => PathValue) & { cwd(): PathValue } = Object.assign(\n"
        "    function Path(value: unknown = \"\"): PathValue {\n"
        "        return _wrap_path_obj(new PathValue(value));\n"
        "    },\n"
        "    {\n"
        "        cwd(): PathValue {\n"
        "            return _wrap_path_obj(PathValue.cwd());\n"
        "        },\n"
        "    },\n"
        ");\n\n"
        "export function pathJoin(base: unknown, child: unknown): PathValue {\n"
        "    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));\n"
        "}\n"
    )


def rewrite_go_program_to_library(go_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(go_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^func\s+main\s*\("))
    text = "\n".join(lines)
    text = re.sub(
        r"(?m)^(\s*)_(?:[A-Za-z0-9]+_)?append_list\((\w+),\s*(.+)\)$",
        r"\1\2 = append(\2, \3...)",
        text,
    )
    text = re.sub(
        r"(?m)^(\s*)_ = open\(",
        r"\1f := open(",
        text,
    )
    return text.rstrip() + "\n"


def rewrite_php_program_to_library(php_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(php_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^function\s+__pytra_main\s*\("))
    out: list[str] = []
    for line in lines:
        line = line.replace(
            "require_once __DIR__ . '/pytra/py_runtime.php';",
            "require_once dirname(__DIR__) . '/py_runtime.php';",
        )
        if line.strip() == "__pytra_main();":
            continue
        out.append(line)
    text = "\n".join(out)
    # PHP 配列は値渡しが既定のため、生成 helper の append_list は参照渡し化する。
    text = re.sub(
        r"(?m)^function\s+(_[A-Za-z0-9]+_append_list)\(\$([A-Za-z_][A-Za-z0-9_]*),\s*(\$[A-Za-z_][A-Za-z0-9_]*)\)\s*\{",
        r"function \1(&$\2, \3) {",
        text,
    )
    return text.rstrip() + "\n"


def rewrite_php_std_time_live_wrapper(php_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(php_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^function\s+__pytra_main\s*\("))
    out: list[str] = []
    for line in lines:
        if line.strip() == "require_once __DIR__ . '/pytra/py_runtime.php';":
            continue
        if line.strip() == "__pytra_main();":
            continue
        out.append(line)
    text = "\n".join(out)
    text = text.replace("function perf_counter() {", "function perf_counter(): float {")
    text = text.replace("return $__t->perf_counter();", "return microtime(true);")
    if "function perf_counter(): float {" not in text:
        raise RuntimeError("generated PHP std/time wrapper is missing perf_counter()")
    return text.rstrip() + "\n"


def rewrite_php_std_math_live_wrapper(php_src: str) -> str:
    text = rewrite_php_program_to_library(php_src)
    text = text.replace(
        "require_once dirname(__DIR__) . '/py_runtime.php';\n",
        "require_once dirname(__DIR__) . '/py_runtime.php';\n\n$pi = pyMathPi();\n$e = pyMathE();\n",
        1,
    )
    signature_replacements = {
        "function sqrt($x) {": "function sqrt($x): float {",
        "function sin($x) {": "function sin($x): float {",
        "function cos($x) {": "function cos($x): float {",
        "function tan($x) {": "function tan($x): float {",
        "function exp($x) {": "function exp($x): float {",
        "function log($x) {": "function log($x): float {",
        "function log10($x) {": "function log10($x): float {",
        "function fabs($x) {": "function fabs($x): float {",
        "function floor($x) {": "function floor($x): float {",
        "function ceil($x) {": "function ceil($x): float {",
        "function pow($x, $y) {": "function pow($x, $y): float {",
    }
    for before, after in signature_replacements.items():
        text = text.replace(before, after)
    if "pyMathPi()" not in text or "pyMathE()" not in text:
        raise RuntimeError("generated PHP std/math wrapper is missing pi/e helpers")
    if "__pytra_main" in text:
        raise RuntimeError("generated PHP std/math wrapper still contains main stub")
    return text.rstrip() + "\n"


def rewrite_php_std_pathlib_live_wrapper(php_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__",
        "parent()",
        "name()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(",
        "read_text(",
        "write_text(",
        "glob(",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in php_src:
            raise RuntimeError("generated PHP std/pathlib wrapper is missing: " + fragment)
    return "\n".join(
        [
            "<?php",
            "declare(strict_types=1);",
            "",
            "require_once dirname(__DIR__) . '/py_runtime.php';",
            "",
            "if (!class_exists('Path', false)) {",
            "    class Path {",
            "        public string $path;",
            "        public string $name;",
            "        public string $stem;",
            "        public string $suffix;",
            "        public $parent;",
            "",
            "        public function __construct($value) {",
            "            $this->path = (string)$value;",
            "            $this->name = basename($this->path);",
            "            $dot = strrpos($this->name, '.');",
            "            $this->stem = ($dot === false || $dot === 0) ? $this->name : substr($this->name, 0, $dot);",
            "            $this->suffix = ($dot === false || $dot === 0) ? '' : substr($this->name, $dot);",
            "            $parentTxt = dirname($this->path);",
            "            if ($parentTxt === '' || $parentTxt === $this->path) {",
            "                $this->parent = null;",
            "            } else {",
            "                $this->parent = new Path($parentTxt);",
            "            }",
            "        }",
            "",
            "        public function __toString(): string {",
            "            return $this->path;",
            "        }",
            "",
            "        public function __fspath__(): string {",
            "            return $this->path;",
            "        }",
            "",
            "        public function __truediv__($rhs): Path {",
            "            $rhsText = (string)$rhs;",
            "            if ($this->path === '') {",
            "                return new Path($rhsText);",
            "            }",
            "            return new Path(rtrim($this->path, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . ltrim($rhsText, DIRECTORY_SEPARATOR));",
            "        }",
            "",
            "        public function resolve(): Path {",
            "            $resolved = realpath($this->path);",
            "            if ($resolved === false) {",
            "                $resolved = $this->path;",
            "            }",
            "            return new Path($resolved);",
            "        }",
            "",
            "        public function exists(): bool {",
            "            return file_exists($this->path);",
            "        }",
            "",
            "        public function mkdir($parents = false, $exist_ok = false): void {",
            "            if ($exist_ok && file_exists($this->path)) {",
            "                return;",
            "            }",
            "            if ((bool)$parents) {",
            "                if (@mkdir($this->path, 0777, true)) {",
            "                    return;",
            "                }",
            "                if ((bool)$exist_ok && is_dir($this->path)) {",
            "                    return;",
            "                }",
            "                throw new RuntimeException('mkdir failed: ' . $this->path);",
            "            }",
            "            if (@mkdir($this->path)) {",
            "                return;",
            "            }",
            "            if ((bool)$exist_ok && is_dir($this->path)) {",
            "                return;",
            "            }",
            "            throw new RuntimeException('mkdir failed: ' . $this->path);",
            "        }",
            "",
            "        public function write_text($text, $encoding = 'utf-8'): int {",
            "            $bytes = file_put_contents($this->path, (string)$text);",
            "            if ($bytes === false) {",
            "                throw new RuntimeException('write_text failed: ' . $this->path);",
            "            }",
            "            return $bytes;",
            "        }",
            "",
            "        public function read_text($encoding = 'utf-8'): string {",
            "            $data = file_get_contents($this->path);",
            "            if ($data === false) {",
            "                throw new RuntimeException('read_text failed: ' . $this->path);",
            "            }",
            "            return $data;",
            "        }",
            "",
            "        public function glob($pattern): array {",
            "            $prefix = rtrim($this->path, DIRECTORY_SEPARATOR);",
            "            $items = glob($prefix . DIRECTORY_SEPARATOR . (string)$pattern);",
            "            if (!is_array($items)) {",
            "                return [];",
            "            }",
            "            return array_map(fn($item) => new Path($item), $items);",
            "        }",
            "",
            "        public static function cwd(): Path {",
            "            return new Path(getcwd());",
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def rewrite_cpp_program_to_namespace(cpp_src: str, namespace_name: str) -> str:
    lines = _strip_trailing_string_literal_expr(cpp_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^static\s+void\s+__pytra_module_init\s*\("))
    lines = _remove_block_by_signature(lines, re.compile(r"^int\s+main\s*\("))

    include_lines: list[str] = []
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        if not in_body and (line.startswith("#") or line.strip() == ""):
            include_lines.append(line)
            continue
        in_body = True
        body_lines.append(line)

    out: list[str] = []
    out.extend(include_lines)
    if len(out) > 0 and out[-1].strip() != "":
        out.append("")
    out.append("namespace " + namespace_name + " {")
    out.append("")
    out.extend(body_lines)
    if len(out) > 0 and out[-1].strip() != "":
        out.append("")
    out.append("}  // namespace " + namespace_name)
    out.append("")
    return "\n".join(out)


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
    elif item.postprocess == "cs_std_time_live_wrapper":
        generated = rewrite_cs_std_time_live_wrapper(generated)
    elif item.postprocess == "java_std_time_live_wrapper":
        generated = rewrite_java_std_time_live_wrapper(generated)
    elif item.postprocess == "java_std_math_live_wrapper":
        generated = rewrite_java_std_math_live_wrapper(generated)
    elif item.postprocess == "js_std_math_live_wrapper":
        generated = rewrite_js_std_math_live_wrapper(generated)
    elif item.postprocess == "js_std_time_live_wrapper":
        generated = rewrite_js_std_time_live_wrapper(generated)
    elif item.postprocess == "js_std_pathlib_live_wrapper":
        generated = rewrite_js_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "ts_std_math_live_wrapper":
        generated = rewrite_ts_std_math_live_wrapper(generated)
    elif item.postprocess == "ts_std_time_live_wrapper":
        generated = rewrite_ts_std_time_live_wrapper(generated)
    elif item.postprocess == "ts_std_pathlib_live_wrapper":
        generated = rewrite_ts_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "js_program_to_cjs_module":
        generated = rewrite_js_program_to_cjs_module(generated)
    elif item.postprocess == "go_program_to_library":
        generated = rewrite_go_program_to_library(generated)
    elif item.postprocess == "php_std_time_live_wrapper":
        generated = rewrite_php_std_time_live_wrapper(generated)
    elif item.postprocess == "php_std_math_live_wrapper":
        generated = rewrite_php_std_math_live_wrapper(generated)
    elif item.postprocess == "php_std_pathlib_live_wrapper":
        generated = rewrite_php_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "php_program_to_library":
        generated = rewrite_php_program_to_library(generated)
    elif item.postprocess == "cpp_program_to_namespace":
        if item.helper_name == "":
            raise RuntimeError("missing helper_name(namespace) for cpp_program_to_namespace: " + item.item_id)
        generated = rewrite_cpp_program_to_namespace(generated, item.helper_name)
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
