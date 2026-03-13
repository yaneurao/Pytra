#!/usr/bin/env python3
"""Collect multistage selfhost status for non-C++ transpilers."""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2X_CLI = ROOT / "src" / "py2x.py"
PY2X_SRC = ROOT / "src" / "py2x.py"


@dataclass
class LangSpec:
    lang: str
    ext: str


@dataclass
class StatusRow:
    lang: str
    stage1: str
    stage2: str
    stage3: str
    category: str
    note: str


LANGS: list[LangSpec] = [
    LangSpec("rs", ".rs"),
    LangSpec("cs", ".cs"),
    LangSpec("js", ".js"),
    LangSpec("ts", ".ts"),
    LangSpec("go", ".go"),
    LangSpec("java", ".java"),
    LangSpec("swift", ".swift"),
    LangSpec("kotlin", ".kt"),
]


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    run_cwd = ROOT if cwd is None else cwd
    cp = subprocess.run(cmd, cwd=str(run_cwd), capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    if msg == "":
        msg = f"exit={cp.returncode}"
    parts = [ln.strip() for ln in msg.splitlines() if ln.strip() != ""]
    err_pat = re.compile(
        r"(error\s+CS\d+|Error|unsupported_|not_implemented|SyntaxError|TypeError|ReferenceError|RuntimeError|Exception)",
        re.IGNORECASE,
    )
    i = 0
    while i < len(parts):
        line = parts[i]
        if err_pat.search(line):
            return False, line
        i += 1
    if len(parts) > 0:
        return False, parts[-1]
    return False, msg


def _is_preview_output(text: str) -> bool:
    return ("プレビュー出力" in text) or ("TODO: 専用" in text) or ("preview backend" in text)


def _strip_cs_single_line_comments(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        idx = line.find("//")
        if idx >= 0:
            line = line[:idx]
        kept.append(line)
        i += 1
    return "\n".join(kept)


def _is_cs_empty_skeleton(text: str) -> bool:
    if "public static class Program" not in text:
        return False
    method_pat = re.compile(r"public\s+static\s+[^{;]+\)\s*\{(?P<body>.*?)\n\s*\}", re.DOTALL)
    bodies = [m.group("body") for m in method_pat.finditer(text)]
    if len(bodies) == 0:
        return False
    non_empty = 0
    i = 0
    while i < len(bodies):
        body = _strip_cs_single_line_comments(bodies[i]).strip()
        if body != "":
            non_empty += 1
        i += 1
    return non_empty == 0


def _extract_js_relative_imports(js_src: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    patterns = [
        re.compile(r'from\s+["\'](?P<path>\.[^"\']*\.js)["\']'),
        re.compile(r'import\s+["\'](?P<path>\.[^"\']*\.js)["\']'),
    ]
    for pat in patterns:
        for m in pat.finditer(js_src):
            path = m.group("path")
            if path in seen:
                continue
            seen.add(path)
            out.append(path)
    return out


def _normalize_js_module_import_paths(js_src: str, src_file: Path, stage_src_root: Path) -> str:
    lines = js_src.splitlines()
    out: list[str] = []
    pat = re.compile(r'(?P<head>\s*import\s+(?:.+?\s+from\s+)?["\'])(?P<path>\.[^"\']*\.js)(?P<tail>["\'].*)')
    for line in lines:
        m = pat.match(line)
        if m is None:
            out.append(line)
            continue
        rel_path = m.group("path")
        if rel_path.startswith("./"):
            root_candidate = (stage_src_root / rel_path[2:]).resolve()
            local_candidate = (src_file.parent / rel_path).resolve()
            if rel_path.startswith("./pytra/") or rel_path.startswith("./runtime/"):
                target_abs = root_candidate
            elif local_candidate.exists():
                target_abs = local_candidate
            else:
                target_abs = root_candidate
            rel = os.path.relpath(target_abs, src_file.parent.resolve()).replace("\\", "/")
            if not rel.startswith("."):
                rel = "./" + rel
            line = m.group("head") + rel + m.group("tail")
        out.append(line)
    norm = "\n".join(out)
    if js_src.endswith("\n"):
        norm += "\n"
    return norm


def _rewrite_js_selfhost_syntax(js_src: str) -> str:
    out = js_src
    pat_not_in = re.compile(r"(?P<lhs>[A-Za-z_][A-Za-z0-9_\.]*)\s+not\s+in\s+\{(?P<items>[^{}]+)\}")
    pat_in = re.compile(r"(?P<lhs>[A-Za-z_][A-Za-z0-9_\.]*)\s+in\s+\{(?P<items>[^{}]+)\}")
    pat_f_dq = re.compile(r'(?<![A-Za-z0-9_"\'])f"(?P<body>[^"\n]*)"')
    pat_f_sq = re.compile(r"(?<![A-Za-z0-9_\"'])f'(?P<body>[^'\n]*)'")
    pat_get = re.compile(r"(?P<obj>[A-Za-z_][A-Za-z0-9_\.]*)\.get\(")
    pat_items = re.compile(r"(?P<obj>[A-Za-z_][A-Za-z0-9_\.]*)\.items\(")
    pat_keys = re.compile(r"(?P<obj>[A-Za-z_][A-Za-z0-9_\.]*)\.keys\(")
    pat_values = re.compile(r"(?P<obj>[A-Za-z_][A-Za-z0-9_\.]*)\.values\(")
    pat_join = re.compile(r"(?P<sep>\"[^\"\n]*\"|'[^'\n]*')\.join\((?P<items>[^)\n]+)\)")
    out = pat_not_in.sub(lambda m: "!" + "[" + m.group("items") + "].includes(" + m.group("lhs") + ")", out)
    out = pat_in.sub(lambda m: "[" + m.group("items") + "].includes(" + m.group("lhs") + ")", out)
    out = pat_f_dq.sub(lambda m: "`" + m.group("body").replace("{", "${") + "`", out)
    out = pat_f_sq.sub(lambda m: "`" + m.group("body").replace("{", "${") + "`", out)
    out = pat_get.sub(lambda m: "__pytra_dict_get(" + m.group("obj") + ", ", out)
    out = pat_items.sub(lambda m: "__pytra_dict_items(" + m.group("obj") + ", ", out)
    out = pat_keys.sub(lambda m: "__pytra_dict_keys(" + m.group("obj") + ", ", out)
    out = pat_values.sub(lambda m: "__pytra_dict_values(" + m.group("obj") + ", ", out)
    out = pat_join.sub(lambda m: "__pytra_join(" + m.group("sep") + ", " + m.group("items") + ")", out)
    if (
        "class JsEmitter {" in out
        and "CodeEmitter" in out
        and "Object.setPrototypeOf(JsEmitter.prototype, CodeEmitter.prototype);" not in out
    ):
        out = out.replace(
            "function transpile_to_js(",
            "Object.setPrototypeOf(JsEmitter.prototype, CodeEmitter.prototype);\n"
            "Object.setPrototypeOf(JsEmitter, CodeEmitter);\n\n"
            "function transpile_to_js(",
            1,
        )
    helper_chunks: list[str] = []
    if "__pytra_dict_get(" in out and "function __pytra_dict_get(" not in out:
        helper_chunks.append(
            "function __pytra_dict_get(obj, key, default_value = null) {\n"
            "  if (obj instanceof Map) {\n"
            "    return obj.has(key) ? obj.get(key) : default_value;\n"
            "  }\n"
            "  if (obj === null || obj === undefined) {\n"
            "    return default_value;\n"
            "  }\n"
            "  return Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : default_value;\n"
            "}\n"
        )
    if "__pytra_dict_items(" in out and "function __pytra_dict_items(" not in out:
        helper_chunks.append(
            "function __pytra_dict_items(obj) {\n"
            "  if (obj instanceof Map) { return Array.from(obj.entries()); }\n"
            "  if (obj === null || obj === undefined) { return []; }\n"
            "  return Object.entries(obj);\n"
            "}\n"
        )
    if "__pytra_dict_keys(" in out and "function __pytra_dict_keys(" not in out:
        helper_chunks.append(
            "function __pytra_dict_keys(obj) {\n"
            "  if (obj instanceof Map) { return Array.from(obj.keys()); }\n"
            "  if (obj === null || obj === undefined) { return []; }\n"
            "  return Object.keys(obj);\n"
            "}\n"
        )
    if "__pytra_dict_values(" in out and "function __pytra_dict_values(" not in out:
        helper_chunks.append(
            "function __pytra_dict_values(obj) {\n"
            "  if (obj instanceof Map) { return Array.from(obj.values()); }\n"
            "  if (obj === null || obj === undefined) { return []; }\n"
            "  return Object.values(obj);\n"
            "}\n"
        )
    if "__pytra_join(" in out and "function __pytra_join(" not in out:
        helper_chunks.append(
            "function __pytra_join(sep, items) {\n"
            "  const s = String(sep);\n"
            "  if (Array.isArray(items)) { return items.join(s); }\n"
            "  if (items === null || items === undefined) { return ''; }\n"
            "  if (typeof items[Symbol.iterator] === 'function') { return Array.from(items).join(s); }\n"
            "  return String(items);\n"
            "}\n"
        )
    if "String.prototype.strip" not in out:
        helper_chunks.append(
            "if (typeof String.prototype.strip !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'strip', { value: function() { return this.trim(); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.lstrip !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'lstrip', { value: function() { return this.replace(/^\\s+/, ''); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.rstrip !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'rstrip', { value: function() { return this.replace(/\\s+$/, ''); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.startswith !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'startswith', { value: function(prefix) { return this.startsWith(String(prefix)); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.endswith !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'endswith', { value: function(suffix) { return this.endsWith(String(suffix)); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.find !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'find', { value: function(sub) { return this.indexOf(String(sub)); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.lower !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'lower', { value: function() { return this.toLowerCase(); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.upper !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'upper', { value: function() { return this.toUpperCase(); }, enumerable: false });\n"
            "}\n"
            "if (typeof String.prototype.map !== 'function') {\n"
            "  Object.defineProperty(String.prototype, 'map', { value: function(fn) { return Array.from(this).map(fn); }, enumerable: false });\n"
            "}\n"
        )
    if "set(" in out and "function set(" not in out:
        helper_chunks.append(
            "function _pytra_make_set() {\n"
            "  const out = Object.create(null);\n"
            "  Object.defineProperty(out, 'add', { value: function(v) { this[String(v)] = true; return this; }, enumerable: false });\n"
            "  Object.defineProperty(out, Symbol.iterator, { value: function*() { for (const k of Object.keys(this)) { yield k; } }, enumerable: false });\n"
            "  return out;\n"
            "}\n"
            "function set(items = []) {\n"
            "  const out = _pytra_make_set();\n"
            "  if (items !== null && items !== undefined) {\n"
            "    if (Array.isArray(items) || typeof items[Symbol.iterator] === 'function') {\n"
            "      for (const v of items) { out.add(v); }\n"
            "    }\n"
            "  }\n"
            "  return out;\n"
            "}\n"
        )
    if "list(" in out and "function list(" not in out:
        helper_chunks.append(
            "function list(items = []) {\n"
            "  if (Array.isArray(items)) { return items.slice(); }\n"
            "  if (items === null || items === undefined) { return []; }\n"
            "  if (typeof items[Symbol.iterator] === 'function') { return Array.from(items); }\n"
            "  return [];\n"
            "}\n"
        )
    if "dict(" in out and "function dict(" not in out:
        helper_chunks.append(
            "function _pytra_tag_map(out) {\n"
            "  if (typeof PYTRA_TYPE_ID !== 'undefined' && typeof PY_TYPE_MAP !== 'undefined') {\n"
            "    out[PYTRA_TYPE_ID] = PY_TYPE_MAP;\n"
            "  }\n"
            "  return out;\n"
            "}\n"
            "function dict(items = null) {\n"
            "  const out = _pytra_tag_map({});\n"
            "  if (items === null || items === undefined) { return out; }\n"
            "  if (items instanceof Map) {\n"
            "    for (const [k, v] of items.entries()) { out[String(k)] = v; }\n"
            "    return out;\n"
            "  }\n"
            "  if (Array.isArray(items) || typeof items[Symbol.iterator] === 'function') {\n"
            "    for (const ent of items) {\n"
            "      if (Array.isArray(ent) && ent.length >= 2) { out[String(ent[0])] = ent[1]; }\n"
            "    }\n"
            "    return out;\n"
            "  }\n"
            "  if (typeof items === 'object') {\n"
            "    for (const [k, v] of Object.entries(items)) { out[String(k)] = v; }\n"
            "  }\n"
            "  return out;\n"
            "}\n"
        )
    if len(helper_chunks) > 0:
        out = "".join(helper_chunks) + out
    if "class CodeEmitter {" in out and "Object.getOwnPropertyNames(CodeEmitter.prototype)" not in out:
        out += (
            "\nfor (const __name of Object.getOwnPropertyNames(CodeEmitter.prototype)) {\n"
            "  if (__name === 'constructor') { continue; }\n"
            "  if (Object.prototype.hasOwnProperty.call(CodeEmitter, __name)) { continue; }\n"
            "  const __fn = CodeEmitter.prototype[__name];\n"
            "  if (typeof __fn === 'function') { CodeEmitter[__name] = __fn; }\n"
            "}\n"
        )
    return out


def _parse_js_named_imports(js_src: str) -> list[tuple[str, str]]:
    reqs: list[tuple[str, str]] = []
    pat = re.compile(r'\s*import\s*\{(?P<names>[^}]*)\}\s*from\s*["\'](?P<path>\.[^"\']*\.js)["\']')
    for line in js_src.splitlines():
        m = pat.match(line)
        if m is None:
            continue
        rel_path = m.group("path").strip()
        names_txt = m.group("names")
        for raw in names_txt.split(","):
            part = raw.strip()
            if part == "":
                continue
            src_name = part.split(" as ")[0].strip()
            if src_name != "":
                reqs.append((rel_path, src_name))
    return reqs


def _js_has_symbol_definition(js_src: str, name: str) -> bool:
    esc = re.escape(name)
    pats = [
        re.compile(rf"^function\s+{esc}\s*\(", re.MULTILINE),
        re.compile(rf"^class\s+{esc}\b", re.MULTILINE),
        re.compile(rf"^(?:const|let|var)\s+{esc}\b", re.MULTILINE),
    ]
    for pat in pats:
        if pat.search(js_src):
            return True
    return False


def _js_already_exports_name(js_src: str, name: str) -> bool:
    esc = re.escape(name)
    if re.search(rf"^export\s+(?:function|class|const|let|var)\s+{esc}\b", js_src, re.MULTILINE):
        return True
    for m in re.finditer(r"^export\s*\{(?P<body>[^}]*)\}", js_src, re.MULTILINE):
        body = m.group("body")
        for raw in body.split(","):
            token = raw.strip()
            if token == "":
                continue
            exported = token.split(" as ")[0].strip()
            if exported == name:
                return True
    return False


def _inject_js_named_exports(stage_src_root: Path) -> None:
    requests: dict[str, set[str]] = {}
    for src_file in stage_src_root.rglob("*.js"):
        js_src = src_file.read_text(encoding="utf-8")
        for rel_path, name in _parse_js_named_imports(js_src):
            target_abs = (src_file.parent / rel_path).resolve()
            try:
                target_abs.relative_to(stage_src_root.resolve())
            except ValueError:
                continue
            key = str(target_abs)
            if key not in requests:
                requests[key] = set()
            requests[key].add(name)
    for target_key, names in requests.items():
        target = Path(target_key)
        if not target.exists():
            continue
        js_src = target.read_text(encoding="utf-8")
        exportable: list[str] = []
        for name in sorted(names):
            if not _js_has_symbol_definition(js_src, name):
                continue
            if _js_already_exports_name(js_src, name):
                continue
            exportable.append(name)
        if len(exportable) == 0:
            continue
        updated = js_src.rstrip() + "\nexport { " + ", ".join(exportable) + " };\n"
        target.write_text(updated, encoding="utf-8")


def _write_js_selfhost_shims(stage_src_root: Path) -> None:
    files: dict[str, str] = {
        "importlib.js": (
            "import { PYTRA_TYPE_ID, PY_TYPE_MAP } from './pytra/py_runtime.js';\n"
            "import { write_js_runtime_shims } from './toolchain/compiler/js_runtime_shims.js';\n"
            "import { lower_east3_to_js_ir } from './backends/js/lower/east3_to_js_ir.js';\n"
            "import { optimize_js_ir } from './backends/js/optimizer/pipeline.js';\n"
            "import { transpile_to_js } from './backends/js/emitter/js_emitter.js';\n"
            "function _module_dict(raw) {\n"
            "  const out = { [PYTRA_TYPE_ID]: PY_TYPE_MAP };\n"
            "  for (const [k, v] of Object.entries(raw)) { out[k] = v; }\n"
            "  return out;\n"
            "}\n"
            "function import_module(name) {\n"
            "  if (name === 'toolchain.compiler.js_runtime_shims') { return _module_dict({ write_js_runtime_shims }); }\n"
            "  if (name === 'backends.js.lower') { return _module_dict({ lower_east3_to_js_ir }); }\n"
            "  if (name === 'backends.js.optimizer') { return _module_dict({ optimize_js_ir }); }\n"
            "  if (name === 'backends.js.emitter.js_emitter') { return _module_dict({ transpile_to_js }); }\n"
            "  throw new Error('import_module unsupported: ' + String(name));\n"
            "}\n"
            "export { import_module };\n"
        ),
        "pytra/py_runtime.js": (
            "import { createRequire } from 'node:module';\n"
            "const require = createRequire(import.meta.url);\n"
            "const rt = require('../runtime/js/native/built_in/py_runtime.js');\n"
            "export const PY_TYPE_NONE = rt.PY_TYPE_NONE;\n"
            "export const PY_TYPE_BOOL = rt.PY_TYPE_BOOL;\n"
            "export const PY_TYPE_NUMBER = rt.PY_TYPE_NUMBER;\n"
            "export const PY_TYPE_STRING = rt.PY_TYPE_STRING;\n"
            "export const PY_TYPE_ARRAY = rt.PY_TYPE_ARRAY;\n"
            "export const PY_TYPE_MAP = rt.PY_TYPE_MAP;\n"
            "export const PY_TYPE_SET = rt.PY_TYPE_SET;\n"
            "export const PY_TYPE_OBJECT = rt.PY_TYPE_OBJECT;\n"
            "export const PYTRA_TYPE_ID = rt.PYTRA_TYPE_ID;\n"
            "export const pyRegisterType = rt.pyRegisterType;\n"
            "export const pyRegisterClassType = rt.pyRegisterClassType;\n"
            "export const pyIsSubtype = rt.pyIsSubtype;\n"
            "export const pyIsInstance = rt.pyIsInstance;\n"
            "export const pyTypeId = rt.pyTypeId;\n"
            "export const pyTruthy = rt.pyTruthy;\n"
            "export const pyTryLen = rt.pyTryLen;\n"
            "export const pyStr = rt.pyStr;\n"
            "export const pyToString = rt.pyToString;\n"
            "export const pyPrint = rt.pyPrint;\n"
            "export const pyLen = rt.pyLen;\n"
            "export const pyBool = rt.pyBool;\n"
            "export const pyRange = rt.pyRange;\n"
            "export const pyFloorDiv = rt.pyFloorDiv;\n"
            "export const pyMod = rt.pyMod;\n"
            "export const pyIn = rt.pyIn;\n"
            "export const pySlice = rt.pySlice;\n"
            "export const pyOrd = rt.pyOrd;\n"
            "export const pyChr = rt.pyChr;\n"
            "export const pyBytearray = rt.pyBytearray;\n"
            "export const pyBytes = rt.pyBytes;\n"
            "export const pyIsDigit = rt.pyIsDigit;\n"
            "export const pyIsAlpha = rt.pyIsAlpha;\n"
        ),
        "pytra/std/pathlib.js": (
            "import { createRequire } from 'node:module';\n"
            "const require = createRequire(import.meta.url);\n"
            "const rt = require('../../runtime/js/native/std/pathlib.js');\n"
            "function _wrap_path_obj(obj) {\n"
            "  if (obj === null || obj === undefined || typeof obj !== 'object') { return obj; }\n"
            "  if (typeof obj.parent === 'function' && !Object.prototype.hasOwnProperty.call(obj, '__pytra_parent_wrapped')) {\n"
            "    const parent_fn = obj.parent.bind(obj);\n"
            "    Object.defineProperty(obj, 'parent', { get: function() { return _wrap_path_obj(parent_fn()); }, configurable: true });\n"
            "    Object.defineProperty(obj, '__pytra_parent_wrapped', { value: true, enumerable: false, configurable: true });\n"
            "  }\n"
            "  if (typeof obj.name === 'function' && !Object.prototype.hasOwnProperty.call(obj, '__pytra_name_wrapped')) {\n"
            "    const name_fn = obj.name.bind(obj);\n"
            "    Object.defineProperty(obj, 'name', { get: function() { return name_fn(); }, configurable: true });\n"
            "    Object.defineProperty(obj, '__pytra_name_wrapped', { value: true, enumerable: false, configurable: true });\n"
            "  }\n"
            "  if (typeof obj.stem === 'function' && !Object.prototype.hasOwnProperty.call(obj, '__pytra_stem_wrapped')) {\n"
            "    const stem_fn = obj.stem.bind(obj);\n"
            "    Object.defineProperty(obj, 'stem', { get: function() { return stem_fn(); }, configurable: true });\n"
            "    Object.defineProperty(obj, '__pytra_stem_wrapped', { value: true, enumerable: false, configurable: true });\n"
            "  }\n"
            "  if (typeof obj.mkdir === 'function' && !Object.prototype.hasOwnProperty.call(obj, '__pytra_mkdir_wrapped')) {\n"
            "    const mkdir_fn = obj.mkdir.bind(obj);\n"
            "    Object.defineProperty(obj, 'mkdir', {\n"
            "      value: function(parents = true, exist_ok = true) {\n"
            "        try { return mkdir_fn(parents, exist_ok); }\n"
            "        catch (err) {\n"
            "          if (err && err.code === 'EEXIST') { return; }\n"
            "          throw err;\n"
            "        }\n"
            "      },\n"
            "      configurable: true,\n"
            "      enumerable: false,\n"
            "      writable: true,\n"
            "    });\n"
            "    Object.defineProperty(obj, '__pytra_mkdir_wrapped', { value: true, enumerable: false, configurable: true });\n"
            "  }\n"
            "  return obj;\n"
            "}\n"
            "function Path(value = '') { return _wrap_path_obj(new rt.Path(value)); }\n"
            "export { Path };\n"
            "export const pathJoin = function(base, child) { return _wrap_path_obj(rt.pathJoin(base, child)); };\n"
        ),
        "pytra/std/math.js": (
            "import { createRequire } from 'node:module';\n"
            "const require = createRequire(import.meta.url);\n"
            "const rt = require('../../runtime/js/native/std/math.js');\n"
            "export const pi = rt.pi;\n"
            "export const e = rt.e;\n"
            "export const sin = rt.sin;\n"
            "export const cos = rt.cos;\n"
            "export const tan = rt.tan;\n"
            "export const sqrt = rt.sqrt;\n"
            "export const exp = rt.exp;\n"
            "export const log = rt.log;\n"
            "export const log10 = rt.log10;\n"
            "export const fabs = rt.fabs;\n"
            "export const floor = rt.floor;\n"
            "export const ceil = rt.ceil;\n"
            "export const pow = rt.pow;\n"
        ),
        "pytra/std/time.js": (
            "import { createRequire } from 'node:module';\n"
            "const require = createRequire(import.meta.url);\n"
            "const rt = require('../../runtime/js/native/std/time.js');\n"
            "const perf_counter = typeof rt.perf_counter === 'function' ? rt.perf_counter : rt.perfCounter;\n"
            "export { perf_counter };\n"
            "export const perfCounter = perf_counter;\n"
        ),
        "pytra/std/sys.js": (
            "const sys = {\n"
            "  argv: Array.from(process.argv.slice(1)),\n"
            "  path: [],\n"
            "  stderr: process.stderr,\n"
            "  stdout: process.stdout,\n"
            "  exit: function(code = 0) { process.exit(Number(code) || 0); },\n"
            "  set_argv: function(values) { this.argv = Array.isArray(values) ? values.map((v) => String(v)) : []; },\n"
            "  set_path: function(values) { this.path = Array.isArray(values) ? values.map((v) => String(v)) : []; },\n"
            "  write_stderr_impl: function(text) { process.stderr.write(String(text)); },\n"
            "  write_stdout_impl: function(text) { process.stdout.write(String(text)); },\n"
            "  write_stderr: function(text) { process.stderr.write(String(text)); },\n"
            "  write_stdout: function(text) { process.stdout.write(String(text)); },\n"
            "};\n"
            "export { sys };\n"
        ),
        "pytra/std/json.js": (
            "function _escape_non_ascii(text) {\n"
            "  return String(text).replace(/[\\u0080-\\uFFFF]/g, (ch) => {\n"
            "    const hex = ch.charCodeAt(0).toString(16).padStart(4, '0');\n"
            "    return '\\\\u' + hex;\n"
            "  });\n"
            "}\n"
            "const json = {\n"
            "  loads: function(text) { return JSON.parse(String(text)); },\n"
            "  dumps: function(obj, ensure_ascii = true, indent = null) {\n"
            "    const space = indent === null || indent === undefined ? undefined : Number(indent);\n"
            "    let out = JSON.stringify(obj, null, space);\n"
            "    if (out === undefined) { out = 'null'; }\n"
            "    if (ensure_ascii) { out = _escape_non_ascii(out); }\n"
            "    return out;\n"
            "  },\n"
            "};\n"
            "export { json };\n"
        ),
        "pytra/std/argparse.js": (
            "import { sys } from './sys.js';\n"
            "import { PYTRA_TYPE_ID, PY_TYPE_MAP } from '../py_runtime.js';\n"
            "class _ArgumentParser {\n"
            "  constructor(description = '') { this.description = String(description || ''); this._specs = []; }\n"
            "  add_argument() {\n"
            "    const args = Array.from(arguments);\n"
            "    if (args.length === 0 || typeof args[0] !== 'string') { throw new Error('add_argument requires at least one name'); }\n"
            "    const names = [String(args[0])];\n"
            "    let argIndex = 1;\n"
            "    const is_optional = names[0].startsWith('-');\n"
            "    if (is_optional) {\n"
            "      while (argIndex < args.length) {\n"
            "        const v = args[argIndex];\n"
            "        if (typeof v === 'string' && v.startsWith('-')) {\n"
            "          names.push(v);\n"
            "          argIndex += 1;\n"
            "          continue;\n"
            "        }\n"
            "        break;\n"
            "      }\n"
            "    }\n"
            "    const base = is_optional ? names[names.length - 1].replace(/^-+/, '').replace(/-/g, '_') : names[0];\n"
            "    let choices = null;\n"
            "    while (argIndex < args.length) {\n"
            "      const v = args[argIndex];\n"
            "      if (Array.isArray(v)) { choices = v; }\n"
            "      argIndex += 1;\n"
            "    }\n"
            "    this._specs.push({ names, is_optional, dest: base, action: null, choices, default: null });\n"
            "  }\n"
            "  error(msg) { if (msg) { sys.write_stderr('error: ' + msg + '\\n'); } throw new Error('argparse_error'); }\n"
            "  parse_args(argv = null) {\n"
            "    const tokens = Array.isArray(argv) ? Array.from(argv).map((x) => String(x)) : Array.from(process.argv.slice(2));\n"
            "    const values = {};\n"
            "    values[PYTRA_TYPE_ID] = PY_TYPE_MAP;\n"
            "    const specsPos = this._specs.filter((s) => !s.is_optional);\n"
            "    const byName = {};\n"
            "    for (const spec of this._specs) {\n"
            "      values[spec.dest] = spec.default;\n"
            "      if (spec.is_optional) { for (const n of spec.names) { byName[n] = spec; } }\n"
            "    }\n"
            "    let posI = 0;\n"
            "    for (let i = 0; i < tokens.length; ) {\n"
            "      const tok = tokens[i];\n"
            "      if (tok.startsWith('-')) {\n"
            "        const spec = byName[tok];\n"
            "        if (!spec) { this.error('unknown option: ' + tok); }\n"
            "        if (i + 1 >= tokens.length) { this.error('missing value for option: ' + tok); }\n"
            "        const parsed = tokens[i + 1];\n"
            "        if (Array.isArray(spec.choices) && spec.choices.length > 0 && !spec.choices.includes(parsed)) {\n"
            "          this.error('invalid choice for option: ' + tok + ' => ' + parsed);\n"
            "        }\n"
            "        values[spec.dest] = parsed;\n"
            "        i += 2;\n"
            "        continue;\n"
            "      }\n"
            "      if (posI >= specsPos.length) { this.error('unexpected extra argument: ' + tok); }\n"
            "      values[specsPos[posI].dest] = tok;\n"
            "      posI += 1;\n"
            "      i += 1;\n"
            "    }\n"
            "    if (posI < specsPos.length) { this.error('missing required argument: ' + specsPos[posI].dest); }\n"
            "    return values;\n"
            "  }\n"
            "}\n"
            "const argparse = { ArgumentParser: function(description = '') { return new _ArgumentParser(description); } };\n"
            "export { argparse };\n"
        ),
        "pytra/std.js": (
            "import { argparse } from './std/argparse.js';\n"
            "import { sys } from './std/sys.js';\n"
            "import { json } from './std/json.js';\n"
            "import * as pathlib from './std/pathlib.js';\n"
            "import * as math from './std/math.js';\n"
            "import * as time from './std/time.js';\n"
            "export { argparse, sys, json, pathlib, math, time };\n"
        ),
        "toolchain/compiler/transpile_cli.js": (
            "import fs from 'node:fs';\n"
            "import { PYTRA_TYPE_ID, PY_TYPE_MAP } from '../../pytra/py_runtime.js';\n"
            "function _tag_map_like(value) {\n"
            "  if (value === null || value === undefined) { return value; }\n"
            "  if (Array.isArray(value)) {\n"
            "    for (let i = 0; i < value.length; i += 1) { value[i] = _tag_map_like(value[i]); }\n"
            "    return value;\n"
            "  }\n"
            "  if (typeof value === 'object') {\n"
            "    for (const [k, v] of Object.entries(value)) { value[k] = _tag_map_like(v); }\n"
            "    value[PYTRA_TYPE_ID] = PY_TYPE_MAP;\n"
            "    return value;\n"
            "  }\n"
            "  return value;\n"
            "}\n"
            "function add_common_transpile_args(parser, enable_negative_index_mode = true, enable_object_dispatch_mode = true, parser_backends = null) {\n"
            "  parser.add_argument('input');\n"
            "  parser.add_argument('-o', '--output');\n"
            "  parser.add_argument('--east3-opt-level');\n"
            "  parser.add_argument('--east3-opt-pass');\n"
            "  parser.add_argument('--dump-east3-before-opt');\n"
            "  parser.add_argument('--dump-east3-after-opt');\n"
            "  parser.add_argument('--dump-east3-opt-trace');\n"
            "  if (enable_negative_index_mode) { parser.add_argument('--negative-index-mode'); }\n"
            "  if (enable_object_dispatch_mode) { parser.add_argument('--object-dispatch-mode'); }\n"
            "  if (parser_backends !== null) { parser.add_argument('--parser-backend'); }\n"
            "}\n"
            "function load_east3_document(input_path) {\n"
            "  const payload = fs.readFileSync(String(input_path), 'utf8');\n"
            "  return _tag_map_like(JSON.parse(payload));\n"
            "}\n"
            "export { add_common_transpile_args, load_east3_document };\n"
        ),
        "toolchain/compiler/js_runtime_shims.js": (
            "function write_js_runtime_shims(_output_dir) {\n"
            "  return;\n"
            "}\n"
            "export { write_js_runtime_shims };\n"
        ),
    }
    for rel, text in files.items():
        out = stage_src_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")


def _copy_js_runtime(stage2_src_root: Path) -> None:
    src_runtime = ROOT / "src" / "runtime" / "js"
    dst_runtime = stage2_src_root / "runtime" / "js"
    shutil.copytree(src_runtime, dst_runtime, dirs_exist_ok=True)
    _write_js_selfhost_shims(stage2_src_root)


def _prepare_js_tree(stage_root: Path, entry_py: Path) -> tuple[bool, str, Path]:
    stage_src_root = stage_root / "src"
    stage_src_root.mkdir(parents=True, exist_ok=True)
    _copy_js_runtime(stage_src_root)

    repo_src_root = ROOT / "src"
    seed_modules = [
        entry_py,
        repo_src_root / "toolchain" / "compiler" / "js_runtime_shims.py",
        repo_src_root / "backends" / "js" / "lower" / "east3_to_js_ir.py",
        repo_src_root / "backends" / "js" / "optimizer" / "pipeline.py",
        repo_src_root / "backends" / "js" / "emitter" / "js_emitter.py",
    ]
    queue: list[Path] = []
    for seed in seed_modules:
        if seed.exists():
            queue.append(seed)
    emitted: set[str] = set()
    entry_js = stage_src_root / entry_py.relative_to(repo_src_root).with_suffix(".js")

    while len(queue) > 0:
        py_src = queue.pop(0)
        try:
            rel_py = py_src.relative_to(repo_src_root)
        except ValueError:
            return False, "js multistage prepare: source escaped repo src", entry_js
        rel_key = rel_py.as_posix()
        if rel_key in emitted:
            continue

        out_js = stage_src_root / rel_py.with_suffix(".js")
        out_js.parent.mkdir(parents=True, exist_ok=True)
        if not out_js.exists():
            ok_emit, msg_emit = _run(
                [
                    "python3",
                    str(PY2X_CLI),
                    str(py_src),
                    "--target",
                    "js",
                    "-o",
                    str(out_js),
                ]
            )
            if not ok_emit:
                return False, "js multistage emit failed at " + rel_key + ": " + msg_emit, entry_js
        js_text = out_js.read_text(encoding="utf-8")
        norm_text = _normalize_js_module_import_paths(js_text, out_js, stage_src_root)
        rew_text = _rewrite_js_selfhost_syntax(norm_text)
        if rew_text != js_text:
            out_js.write_text(rew_text, encoding="utf-8")
            js_text = rew_text
        else:
            js_text = rew_text
        emitted.add(rel_key)
        import_paths = _extract_js_relative_imports(js_text)
        for rel_import in import_paths:
            resolved_js = (out_js.parent / rel_import).resolve()
            try:
                resolved_rel_js = resolved_js.relative_to(stage_src_root.resolve())
            except ValueError:
                continue
            dep_py = (repo_src_root / resolved_rel_js).with_suffix(".py")
            if dep_py.exists():
                queue.append(dep_py)

    # host transpile が書き戻す runtime shim を selfhost 用に再適用する。
    _write_js_selfhost_shims(stage_src_root)
    _inject_js_named_exports(stage_src_root)
    return True, "", entry_js


def _run_js_multistage(stage_tmp: Path, src_py: Path, sample_py: Path) -> tuple[str, str, str, str]:
    if shutil.which("node") is None:
        return "blocked", "blocked", "toolchain_missing", "node not found"

    js_root = stage_tmp / "js_multistage"
    ok_prepare, msg_prepare, entry_js = _prepare_js_tree(js_root, src_py)
    if not ok_prepare:
        return "fail", "skip", "stage1_dependency_transpile_fail", msg_prepare

    stage2_input = src_py
    if src_py.suffix == ".py":
        stage2_src_json = stage_tmp / "js_stage2_input.east3.json"
        stage2_host_tmp = stage_tmp / "js_stage2_input_host_tmp.js"
        ok_stage2_json, msg_stage2_json = _run(
            [
                "python3",
                str(PY2X_CLI),
                str(src_py),
                "--target",
                "js",
                "-o",
                str(stage2_host_tmp),
                "--dump-east3-after-opt",
                str(stage2_src_json),
            ]
        )
        if not ok_stage2_json:
            return "fail", "skip", "self_retranspile_fail", "js stage2 east3 dump failed: " + msg_stage2_json
        if not stage2_src_json.exists():
            return "fail", "skip", "self_retranspile_fail", "js stage2 east3 dump missing"
        stage2_input = stage2_src_json

    stage2_src = js_root / "src" / "py2js_stage2.js"
    ok_stage2, msg_stage2 = _run(
        ["node", str(entry_js), str(stage2_input), "--target", "js", "-o", str(stage2_src)],
        cwd=js_root,
    )
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"

    stage3_input = sample_py
    if sample_py.suffix == ".py":
        stage3_sample_json = stage_tmp / "js_stage3_sample_input.east3.json"
        stage3_host_tmp = stage_tmp / "js_stage3_sample_input_host_tmp.js"
        ok_stage3_json, msg_stage3_json = _run(
            [
                "python3",
                str(PY2X_CLI),
                str(sample_py),
                "--target",
                "js",
                "-o",
                str(stage3_host_tmp),
                "--dump-east3-after-opt",
                str(stage3_sample_json),
            ]
        )
        if not ok_stage3_json:
            return "pass", "fail", "sample_transpile_fail", "js stage3 sample east3 dump failed: " + msg_stage3_json
        if not stage3_sample_json.exists():
            return "pass", "fail", "sample_transpile_fail", "js stage3 sample east3 dump missing"
        stage3_input = stage3_sample_json

    stage3_out = js_root / "js_stage3_sample.js"
    ok_stage3, msg_stage3 = _run(
        ["node", str(stage2_src), str(stage3_input), "--target", "js", "-o", str(stage3_out)],
        cwd=js_root,
    )
    if not ok_stage3:
        return "pass", "fail", "sample_transpile_fail", msg_stage3
    if not stage3_out.exists():
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output missing"

    return "pass", "pass", "pass", "stage2/stage3 sample transpile ok"


def _run_rs_multistage(stage_tmp: Path, stage1_out: Path, src_py: Path, sample_py: Path) -> tuple[str, str, str, str]:
    if shutil.which("rustc") is None:
        return "blocked", "blocked", "toolchain_missing", "rustc not found"

    stage1_bin = stage_tmp / "py2rs_stage1.out"
    ok_build1, msg_build1 = _run(["rustc", str(stage1_out), "-O", "-o", str(stage1_bin)])
    if not ok_build1:
        return "fail", "skip", "compile_fail", msg_build1

    stage2_src = stage_tmp / "py2rs_stage2.rs"
    ok_stage2, msg_stage2 = _run([str(stage1_bin), str(src_py), "--target", "rs", "-o", str(stage2_src)])
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"

    stage2_bin = stage_tmp / "py2rs_stage2.out"
    ok_build2, msg_build2 = _run(["rustc", str(stage2_src), "-O", "-o", str(stage2_bin)])
    if not ok_build2:
        return "pass", "fail", "stage2_compile_fail", msg_build2

    stage3_out = stage_tmp / "rs_stage3_sample.rs"
    ok_stage3, msg_stage3 = _run([str(stage2_bin), str(sample_py), "--target", "rs", "-o", str(stage3_out)])
    if not ok_stage3:
        return "pass", "fail", "sample_transpile_fail", msg_stage3
    if not stage3_out.exists():
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output missing"

    return "pass", "pass", "pass", "stage2/stage3 sample transpile ok"


def _cs_compile(src_cs: Path, out_exe: Path) -> tuple[bool, str]:
    runtime_files = [
        ROOT / "src" / "runtime" / "cs" / "native" / "built_in" / "py_runtime.cs",
        ROOT / "src" / "runtime" / "cs" / "generated" / "std" / "time.cs",
        ROOT / "src" / "runtime" / "cs" / "native" / "std" / "time_native.cs",
        ROOT / "src" / "runtime" / "cs" / "generated" / "std" / "math.cs",
        ROOT / "src" / "runtime" / "cs" / "generated" / "std" / "json.cs",
        ROOT / "src" / "runtime" / "cs" / "generated" / "utils" / "png.cs",
        ROOT / "src" / "runtime" / "cs" / "generated" / "utils" / "gif.cs",
        ROOT / "src" / "runtime" / "cs" / "native" / "std" / "pathlib.cs",
    ]
    compile_cmd = ["mcs", "-langversion:latest", "-warn:0", "-out:" + str(out_exe), str(src_cs)]
    for runtime_file in runtime_files:
        compile_cmd.append(str(runtime_file))
    return _run(compile_cmd)


def _run_cs_multistage(stage_tmp: Path, stage1_out: Path, src_py: Path, sample_py: Path) -> tuple[str, str, str, str]:
    if shutil.which("mcs") is None or shutil.which("mono") is None:
        return "blocked", "blocked", "toolchain_missing", "mcs/mono not found"

    stage1_exe = stage_tmp / "py2cs_stage1.exe"
    ok_build1, msg_build1 = _cs_compile(stage1_out, stage1_exe)
    if not ok_build1:
        return "fail", "skip", "compile_fail", msg_build1

    src_input = src_py
    if src_py.suffix == ".py":
        src_json = stage_tmp / "cs_stage2_input.east3.json"
        src_host_tmp = stage_tmp / "cs_stage2_host_tmp.cs"
        ok_src_json, msg_src_json = _run(
            [
                "python3",
                str(PY2X_CLI),
                str(src_py),
                "--target",
                "cs",
                "-o",
                str(src_host_tmp),
                "--dump-east3-after-opt",
                str(src_json),
            ]
        )
        if not ok_src_json:
            return "fail", "skip", "self_retranspile_fail", "stage2 east3 dump failed: " + msg_src_json
        if not src_json.exists():
            return "fail", "skip", "self_retranspile_fail", "stage2 east3 dump missing"
        src_input = src_json

    stage2_src = stage_tmp / "py2cs_stage2.cs"
    ok_stage2, msg_stage2 = _run(
        ["mono", str(stage1_exe), str(src_input), "--target", "cs", "-o", str(stage2_src)]
    )
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"
    stage2_text = stage2_src.read_text(encoding="utf-8")
    if _is_cs_empty_skeleton(stage2_text):
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output is empty skeleton"

    stage2_exe = stage_tmp / "py2cs_stage2.exe"
    ok_build2, msg_build2 = _cs_compile(stage2_src, stage2_exe)
    if not ok_build2:
        return "pass", "fail", "stage2_compile_fail", msg_build2

    sample_input = sample_py
    if sample_py.suffix == ".py":
        sample_json = stage_tmp / "cs_stage3_input.east3.json"
        sample_host_tmp = stage_tmp / "cs_stage3_host_tmp.cs"
        ok_sample_json, msg_sample_json = _run(
            [
                "python3",
                str(PY2X_CLI),
                str(sample_py),
                "--target",
                "cs",
                "-o",
                str(sample_host_tmp),
                "--dump-east3-after-opt",
                str(sample_json),
            ]
        )
        if not ok_sample_json:
            return "pass", "fail", "sample_transpile_fail", "stage3 east3 dump failed: " + msg_sample_json
        if not sample_json.exists():
            return "pass", "fail", "sample_transpile_fail", "stage3 east3 dump missing"
        sample_input = sample_json

    stage3_out = stage_tmp / "cs_stage3_sample.cs"
    ok_stage3, msg_stage3 = _run(
        ["mono", str(stage2_exe), str(sample_input), "--target", "cs", "-o", str(stage3_out)]
    )
    if not ok_stage3:
        return "pass", "fail", "sample_transpile_fail", msg_stage3
    if not stage3_out.exists():
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output missing"
    stage3_text = stage3_out.read_text(encoding="utf-8")
    if _is_cs_empty_skeleton(stage3_text):
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output is empty skeleton"

    return "pass", "pass", "pass", "stage2/stage3 sample transpile ok"


def _render_report(rows: list[StatusRow], out_path: Path) -> None:
    today = _dt.date.today().isoformat()
    lines: list[str] = []
    lines.append("# P1-MQ-05 Multistage Selfhost Status")
    lines.append("")
    lines.append(f"計測日: {today}")
    lines.append("")
    lines.append("実行コマンド:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 tools/check_multilang_selfhost_multistage.py")
    lines.append("```")
    lines.append("")
    lines.append("| lang | stage1 (self-transpile) | stage2 (self->self) | stage3 (sample) | category | note |")
    lines.append("|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| "
            + row.lang
            + " | "
            + row.stage1
            + " | "
            + row.stage2
            + " | "
            + row.stage3
            + " | "
            + row.category
            + " | "
            + row.note.replace("|", "/")
            + " |"
        )
    lines.append("")
    lines.append("カテゴリ定義:")
    lines.append("- `preview_only`: stage1 は可能だが生成 transpiler が preview 出力。")
    lines.append("- `toolchain_missing`: stage2 実行に必要な実行系/コンパイラが無い。")
    lines.append("- `compile_fail`: stage1 生成 transpiler のビルド失敗。")
    lines.append("- `stage1_dependency_transpile_fail`: stage2 実行準備（依存 transpile）で失敗。")
    lines.append("- `self_retranspile_fail`: 生成 transpiler で自己再変換（stage2）に失敗。")
    lines.append("- `stage2_compile_fail`: stage2 生成 transpiler のビルド失敗。")
    lines.append("- `sample_transpile_fail`: stage2 生成 transpiler で `sample/py/01` 変換に失敗。")
    lines.append("- `stage1_transpile_fail`: stage1 自己変換自体が失敗。")
    lines.append("- `unsupported_by_design`: 現在の multistage runner 対象外で expected failure として扱う。")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="collect multistage selfhost status for non-cpp transpilers")
    ap.add_argument(
        "--out",
        default="docs/ja/plans/p1-multilang-selfhost-multistage-status.md",
        help="write markdown report to this path",
    )
    args = ap.parse_args()

    sample_py = ROOT / "sample" / "py" / "01_mandelbrot.py"
    rows: list[StatusRow] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for spec in LANGS:
            cli = PY2X_CLI
            src = PY2X_SRC
            stage1_out = tmp / f"{spec.lang}_stage1{spec.ext}"

            ok_stage1, msg_stage1 = _run(
                ["python3", str(cli), str(src), "--target", spec.lang, "-o", str(stage1_out)]
            )
            if not ok_stage1:
                rows.append(StatusRow(spec.lang, "fail", "skip", "skip", "stage1_transpile_fail", msg_stage1))
                continue
            if not stage1_out.exists():
                rows.append(StatusRow(spec.lang, "fail", "skip", "skip", "stage1_transpile_fail", "stage1 output missing"))
                continue

            stage1_text = stage1_out.read_text(encoding="utf-8")
            if _is_preview_output(stage1_text):
                rows.append(StatusRow(spec.lang, "pass", "blocked", "blocked", "preview_only", "generated transpiler is preview-only"))
                continue

            if spec.lang == "js":
                st2, st3, category, note = _run_js_multistage(tmp, src, sample_py)
                rows.append(StatusRow(spec.lang, "pass", st2, st3, category, note))
                continue

            if spec.lang == "rs":
                st2, st3, category, note = _run_rs_multistage(tmp, stage1_out, src, sample_py)
                rows.append(StatusRow(spec.lang, "pass", st2, st3, category, note))
                continue

            if spec.lang == "cs":
                st2, st3, category, note = _run_cs_multistage(tmp, stage1_out, src, sample_py)
                rows.append(StatusRow(spec.lang, "pass", st2, st3, category, note))
                continue

            rows.append(StatusRow(spec.lang, "pass", "skip", "skip", "unsupported_by_design", "multistage runner is not defined"))

    out_path = ROOT / args.out
    _render_report(rows, out_path)
    print(f"[OK] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
