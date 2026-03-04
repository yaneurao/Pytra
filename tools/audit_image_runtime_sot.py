#!/usr/bin/env python3
"""Audit PNG/GIF runtime source-of-truth status per language.

This checks whether runtime implementations that expose image helpers
(`write_rgb_png`, `save_gif`, `grayscale_palette`) carry explicit markers
pointing to `src/pytra/utils/png.py` / `src/pytra/utils/gif.py`.
Optionally probes whether each target can transpile those Python sources.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IMAGE_SYMBOL_RE = re.compile(
    r"(write_rgb_png|save_gif|grayscale_palette|py_write_rgb_png|py_save_gif|py_grayscale_palette)"
)
PYTRA_UTILS_SOURCE_RE = re.compile(r"source:\s*src/pytra/utils/(png|gif)\.py", re.IGNORECASE)


@dataclass(frozen=True)
class LangSpec:
    target: str
    runtime_paths: tuple[str, ...]


LANG_SPECS: dict[str, LangSpec] = {
    "cpp": LangSpec(
        target="cpp",
        runtime_paths=(
            "src/runtime/cpp/pytra-gen/utils/png.cpp",
            "src/runtime/cpp/pytra-gen/utils/gif.cpp",
        ),
    ),
    "rs": LangSpec(target="rs", runtime_paths=("src/runtime/rs/pytra/built_in/py_runtime.rs",)),
    "cs": LangSpec(
        target="cs",
        runtime_paths=(
            "src/runtime/cs/pytra/utils/png_helper.cs",
            "src/runtime/cs/pytra/utils/gif_helper.cs",
        ),
    ),
    "js": LangSpec(
        target="js",
        runtime_paths=(
            "src/runtime/js/pytra/png_helper.js",
            "src/runtime/js/pytra/gif_helper.js",
        ),
    ),
    "ts": LangSpec(
        target="ts",
        runtime_paths=(
            "src/runtime/ts/pytra/png_helper.ts",
            "src/runtime/ts/pytra/gif_helper.ts",
        ),
    ),
    "go": LangSpec(target="go", runtime_paths=("src/runtime/go/pytra/py_runtime.go",)),
    "java": LangSpec(target="java", runtime_paths=("src/runtime/java/pytra/built_in/PyRuntime.java",)),
    "swift": LangSpec(target="swift", runtime_paths=("src/runtime/swift/pytra/py_runtime.swift",)),
    "kotlin": LangSpec(target="kotlin", runtime_paths=("src/runtime/kotlin/pytra/py_runtime.kt",)),
    "ruby": LangSpec(target="ruby", runtime_paths=("src/runtime/ruby/pytra/py_runtime.rb",)),
    "lua": LangSpec(target="lua", runtime_paths=("src/runtime/lua/pytra/py_runtime.lua",)),
    "scala": LangSpec(target="scala", runtime_paths=("src/runtime/scala/pytra/py_runtime.scala",)),
    "php": LangSpec(
        target="php",
        runtime_paths=(
            "src/runtime/php/pytra/runtime/png.php",
            "src/runtime/php/pytra/runtime/gif.php",
            "src/runtime/php/pytra/py_runtime.php",
        ),
    ),
    "nim": LangSpec(target="nim", runtime_paths=("src/runtime/nim/pytra/py_runtime.nim",)),
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _scan_runtime(paths: tuple[str, ...]) -> tuple[list[dict[str, object]], bool]:
    rows: list[dict[str, object]] = []
    has_marker = False
    for rel in paths:
        p = ROOT / rel
        if not p.exists():
            rows.append({"path": rel, "exists": False, "has_image_symbols": False, "has_pytra_utils_source_marker": False})
            continue
        txt = _read_text(p)
        has_symbols = IMAGE_SYMBOL_RE.search(txt) is not None
        has_source = PYTRA_UTILS_SOURCE_RE.search(txt) is not None
        has_marker = has_marker or has_source
        rows.append(
            {
                "path": rel,
                "exists": True,
                "has_image_symbols": has_symbols,
                "has_pytra_utils_source_marker": has_source,
            }
        )
    return rows, has_marker


def _probe_transpile(target: str, module_rel: str) -> dict[str, object]:
    src = ROOT / module_rel
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"probe_{target}.txt"
        cp = subprocess.run(
            ["python3", "src/py2x.py", str(src), "--target", target, "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    ok = cp.returncode == 0
    msg = ""
    if not ok:
        msg_raw = cp.stderr.strip() or cp.stdout.strip() or f"exit={cp.returncode}"
        msg = msg_raw.splitlines()[0]
    return {"ok": ok, "error": msg}


def run_audit(probe_transpile: bool) -> dict[str, object]:
    result: dict[str, object] = {"languages": {}, "summary": {}}
    compliant = 0
    non_compliant = 0

    for lang in sorted(LANG_SPECS.keys()):
        spec = LANG_SPECS[lang]
        runtime_rows, has_marker = _scan_runtime(spec.runtime_paths)
        status = "compliant_marker_present" if has_marker else "non_compliant_marker_missing"
        if has_marker:
            compliant += 1
        else:
            non_compliant += 1

        entry: dict[str, object] = {
            "target": spec.target,
            "runtime_scan": runtime_rows,
            "status": status,
        }
        if probe_transpile:
            entry["transpile_probe"] = {
                "png": _probe_transpile(spec.target, "src/pytra/utils/png.py"),
                "gif": _probe_transpile(spec.target, "src/pytra/utils/gif.py"),
            }
        result["languages"][lang] = entry

    result["summary"] = {
        "language_total": len(LANG_SPECS),
        "compliant_marker_present": compliant,
        "non_compliant_marker_missing": non_compliant,
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="audit PNG/GIF runtime source-of-truth status")
    ap.add_argument("--probe-transpile", action="store_true", help="probe py2x transpile for src/pytra/utils/{png,gif}.py")
    ap.add_argument("--summary-json", default="", help="optional output path for json summary")
    args = ap.parse_args()

    report = run_audit(args.probe_transpile)

    summary = report.get("summary", {})
    print(
        "summary: "
        + f"languages={summary.get('language_total', 0)} "
        + f"compliant={summary.get('compliant_marker_present', 0)} "
        + f"non_compliant={summary.get('non_compliant_marker_missing', 0)}"
    )
    langs = report.get("languages", {})
    if isinstance(langs, dict):
        for lang in sorted(langs.keys()):
            entry = langs.get(lang)
            if not isinstance(entry, dict):
                continue
            print(f"- {lang}: {entry.get('status')}")
            probe = entry.get("transpile_probe")
            if isinstance(probe, dict):
                png = probe.get("png")
                gif = probe.get("gif")
                if isinstance(png, dict) and isinstance(gif, dict):
                    print(
                        "  probe: "
                        + f"png={'ok' if png.get('ok') else 'fail'} "
                        + f"gif={'ok' if gif.get('ok') else 'fail'}"
                    )

    if args.summary_json != "":
        out = Path(args.summary_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

