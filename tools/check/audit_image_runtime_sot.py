#!/usr/bin/env python3
"""Audit image runtime layout (`native` / `generated`) per language.

Checks:
- `native` must not contain image encoder core symbols.
- `generated` must contain image runtime symbols.
- image runtime files in `generated` must include:
  - `source: src/pytra/utils/png.py` or `source: src/pytra/utils/gif.py`
  - `generated-by: ...`

Optional:
- Probe transpile for canonical Python sources per target.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

GEN_IMAGE_SYMBOL_RE = re.compile(
    r"(write_rgb_png|save_gif|grayscale_palette|py_write_rgb_png|py_save_gif|py_grayscale_palette|pyWriteRGBPNG|pySaveGIF|pySaveGif|pyGrayscalePalette|__pytra_write_rgb_png|__pytra_save_gif|__pytra_grayscale_palette)"
)
CORE_FORBIDDEN_SYMBOL_RE = re.compile(
    r"(png_crc32|png_adler32|gif_lzw_encode|zlib_store_compress|pyChunk|pyAdler32|pyZlibDeflateStore|pyLzwEncode|pytraGifLzwEncode|pytraCrc32|pytraAdler32)"
)
SOURCE_MARKER_RE = re.compile(r"source:\s*src/pytra/utils/(png|gif)\.py", re.IGNORECASE)
GENERATED_BY_RE = re.compile(r"generated-by:\s*", re.IGNORECASE)
CORE_MIX_REASON = "core_contains_image_symbols"
GEN_MARKER_MISSING_REASONS = {"gen_missing_image_symbols", "gen_missing_source_marker", "gen_missing_generated_by_marker"}
UNRESOLVED_MARKER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("unsupported_stmt", re.compile(r"unsupported stmt", re.IGNORECASE)),
    ("unknown_expr", re.compile(r"unknown expr", re.IGNORECASE)),
    ("fstring_residual", re.compile(r"\bf\"")),
    ("python_to_bytes_call", re.compile(r"\.to_bytes\(")),
    ("python_extend_method", re.compile(r"\.extend\(")),
)


@dataclass(frozen=True)
class LangSpec:
    target: str
    runtime_root: str


LANG_SPECS: dict[str, LangSpec] = {
    "cpp": LangSpec(target="cpp", runtime_root="src/runtime/cpp"),
    "rs": LangSpec(target="rs", runtime_root="src/runtime/rs"),
    "cs": LangSpec(target="cs", runtime_root="src/runtime/cs"),
    "js": LangSpec(target="js", runtime_root="src/runtime/js"),
    "ts": LangSpec(target="ts", runtime_root="src/runtime/ts"),
    "go": LangSpec(target="go", runtime_root="src/runtime/go"),
    "java": LangSpec(target="java", runtime_root="src/runtime/java"),
    "swift": LangSpec(target="swift", runtime_root="src/runtime/swift"),
    "kotlin": LangSpec(target="kotlin", runtime_root="src/runtime/kotlin"),
    "ruby": LangSpec(target="ruby", runtime_root="src/runtime/ruby"),
    "lua": LangSpec(target="lua", runtime_root="src/runtime/lua"),
    "scala": LangSpec(target="scala", runtime_root="src/runtime/scala"),
    "php": LangSpec(target="php", runtime_root="src/runtime/php"),
    "nim": LangSpec(target="nim", runtime_root="src/runtime/nim"),
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _collect_output_text(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")
    if not path.is_dir():
        return ""
    parts: list[str] = []
    for child in sorted(path.rglob("*")):
        if not child.is_file():
            continue
        if child.suffix.lower() in {".o", ".a", ".so", ".dll", ".exe", ".png", ".gif", ".jpg", ".jpeg", ".class"}:
            continue
        parts.append(child.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def _scan_tree_for_symbols(root: Path, symbol_re: re.Pattern[str]) -> list[str]:
    hits: list[str] = []
    if not root.exists() or not root.is_dir():
        return hits
    for child in sorted(root.rglob("*")):
        if not child.is_file():
            continue
        txt = _read_text(child)
        if symbol_re.search(txt) is not None:
            hits.append(str(child.relative_to(ROOT)))
    return hits


def _scan_gen_markers(gen_root: Path) -> tuple[list[str], list[str], list[str]]:
    image_files: list[str] = []
    missing_source: list[str] = []
    missing_generated_by: list[str] = []
    if not gen_root.exists() or not gen_root.is_dir():
        return image_files, missing_source, missing_generated_by
    for child in sorted(gen_root.rglob("*")):
        if not child.is_file():
            continue
        txt = _read_text(child)
        if GEN_IMAGE_SYMBOL_RE.search(txt) is None:
            continue
        rel = str(child.relative_to(ROOT))
        image_files.append(rel)
        if SOURCE_MARKER_RE.search(txt) is None:
            missing_source.append(rel)
        if GENERATED_BY_RE.search(txt) is None:
            missing_generated_by.append(rel)
    return image_files, missing_source, missing_generated_by


def _scan_runtime_layout(spec: LangSpec) -> dict[str, object]:
    runtime_root = ROOT / spec.runtime_root
    core_root = runtime_root / "native"
    gen_root = runtime_root / "generated"
    compat_root = runtime_root / "pytra"

    core_hits = _scan_tree_for_symbols(core_root, CORE_FORBIDDEN_SYMBOL_RE)
    gen_hits, gen_missing_source, gen_missing_generated_by = _scan_gen_markers(gen_root)

    reasons: list[str] = []
    if not core_root.exists():
        reasons.append("core_root_missing")
    if not gen_root.exists():
        reasons.append("gen_root_missing")
    if len(core_hits) > 0:
        reasons.append(CORE_MIX_REASON)
    if len(gen_hits) == 0:
        reasons.append("gen_missing_image_symbols")
    if len(gen_missing_source) > 0:
        reasons.append("gen_missing_source_marker")
    if len(gen_missing_generated_by) > 0:
        reasons.append("gen_missing_generated_by_marker")
    status = "compliant_core_gen_layout" if len(reasons) == 0 else "non_compliant_core_gen_layout"
    return {
        "status": status,
        "reasons": reasons,
        "paths": {
            "runtime_root": spec.runtime_root,
            "core_root": str(core_root.relative_to(ROOT)),
            "gen_root": str(gen_root.relative_to(ROOT)),
            "compat_root": str(compat_root.relative_to(ROOT)),
        },
        "scan": {
            "core_image_symbol_files": core_hits,
            "gen_image_symbol_files": gen_hits,
            "gen_missing_source_marker_files": gen_missing_source,
            "gen_missing_generated_by_files": gen_missing_generated_by,
        },
    }


def _probe_transpile(target: str, module_rel: str) -> dict[str, object]:
    src = ROOT / module_rel
    out_text = ""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"probe_{target}.txt"
        cp = subprocess.run(
            ["python3", "src/pytra-cli.py", str(src), "--target", target, "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode == 0 and out.exists():
            out_text = _collect_output_text(out)
    ok = cp.returncode == 0
    msg = ""
    risk_counts: dict[str, int] = {}
    if not ok:
        msg_raw = cp.stderr.strip() or cp.stdout.strip() or f"exit={cp.returncode}"
        lines = [ln.strip() for ln in msg_raw.splitlines() if ln.strip() != ""]
        msg = lines[-1] if len(lines) > 0 else msg_raw
    else:
        for key, pat in UNRESOLVED_MARKER_PATTERNS:
            hits = len(pat.findall(out_text))
            if hits > 0:
                risk_counts[key] = hits
    return {
        "ok": ok,
        "error": msg,
        "risk_counts": risk_counts,
        "risk_total": sum(risk_counts.values()),
    }


def run_audit(probe_transpile: bool) -> dict[str, object]:
    result: dict[str, object] = {"languages": {}, "summary": {}}
    compliant = 0
    non_compliant = 0

    for lang in sorted(LANG_SPECS.keys()):
        spec = LANG_SPECS[lang]
        entry = _scan_runtime_layout(spec)
        if entry.get("status") == "compliant_core_gen_layout":
            compliant += 1
        else:
            non_compliant += 1

        if probe_transpile:
            entry["transpile_probe"] = {
                "png": _probe_transpile(spec.target, "src/pytra/utils/png.py"),
                "gif": _probe_transpile(spec.target, "src/pytra/utils/gif.py"),
            }
        result["languages"][lang] = entry

    result["summary"] = {
        "language_total": len(LANG_SPECS),
        "compliant_core_gen_layout": compliant,
        "non_compliant_core_gen_layout": non_compliant,
    }
    return result


def collect_guardrail_failures(
    report: dict[str, object],
    *,
    fail_on_core_mix: bool,
    fail_on_gen_markers: bool,
    fail_on_non_compliant: bool,
) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {"core_mix": [], "gen_markers": [], "non_compliant": []}
    langs = report.get("languages", {})
    if not isinstance(langs, dict):
        return failures
    for lang in sorted(langs.keys()):
        entry = langs.get(lang)
        if not isinstance(entry, dict):
            continue
        reasons_any = entry.get("reasons")
        reasons = reasons_any if isinstance(reasons_any, list) else []
        if fail_on_core_mix and CORE_MIX_REASON in reasons:
            failures["core_mix"].append(lang)
        if fail_on_gen_markers and any(str(reason) in GEN_MARKER_MISSING_REASONS for reason in reasons):
            failures["gen_markers"].append(lang)
        if fail_on_non_compliant and len(reasons) > 0:
            failures["non_compliant"].append(lang)
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description="audit image runtime core/gen layout status")
    ap.add_argument("--probe-transpile", action="store_true", help="probe py2x transpile for src/pytra/utils/{png,gif}.py")
    ap.add_argument("--summary-json", default="", help="optional output path for json summary")
    ap.add_argument(
        "--fail-on-core-mix",
        action="store_true",
        help="exit non-zero if any pytra-core contains image encoder symbols",
    )
    ap.add_argument(
        "--fail-on-gen-markers",
        action="store_true",
        help="exit non-zero if pytra-gen image runtime is missing source/generated-by markers",
    )
    ap.add_argument(
        "--fail-on-non-compliant",
        action="store_true",
        help="exit non-zero if any language has non-compliant core/gen layout reasons",
    )
    args = ap.parse_args()

    report = run_audit(args.probe_transpile)
    summary = report.get("summary", {})
    print(
        "summary: "
        + f"languages={summary.get('language_total', 0)} "
        + f"compliant={summary.get('compliant_core_gen_layout', 0)} "
        + f"non_compliant={summary.get('non_compliant_core_gen_layout', 0)}"
    )
    langs = report.get("languages", {})
    if isinstance(langs, dict):
        for lang in sorted(langs.keys()):
            entry = langs.get(lang)
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status"))
            reasons_any = entry.get("reasons")
            reasons = reasons_any if isinstance(reasons_any, list) else []
            suffix = ""
            if len(reasons) > 0:
                suffix = " reasons=" + ",".join(str(r) for r in reasons)
            print("- " + lang + ": " + status + suffix)
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

    failures = collect_guardrail_failures(
        report,
        fail_on_core_mix=bool(args.fail_on_core_mix),
        fail_on_gen_markers=bool(args.fail_on_gen_markers),
        fail_on_non_compliant=bool(args.fail_on_non_compliant),
    )
    if len(failures["core_mix"]) > 0:
        print("[FAIL] pytra-core image symbol detected in: " + ", ".join(failures["core_mix"]))
        return 1
    if len(failures["gen_markers"]) > 0:
        print("[FAIL] pytra-gen marker missing in: " + ", ".join(failures["gen_markers"]))
        return 1
    if len(failures["non_compliant"]) > 0:
        print("[FAIL] non-compliant core/gen layout in: " + ", ".join(failures["non_compliant"]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
