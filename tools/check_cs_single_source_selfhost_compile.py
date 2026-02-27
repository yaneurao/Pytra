#!/usr/bin/env python3
"""Check and summarize single-source C# selfhost compile status."""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "tools" / "prepare_selfhost_source_cs.py"
PY2CS = ROOT / "src" / "py2cs.py"
SELFHOST_PY2CS = ROOT / "selfhost" / "py2cs.py"
RUNTIME_FILES = [
    ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "py_runtime.cs",
    ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "time.cs",
    ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "math.cs",
    ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "png_helper.cs",
    ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "gif_helper.cs",
    ROOT / "src" / "runtime" / "cs" / "pytra" / "std" / "pathlib.cs",
]


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    run_cwd = ROOT if cwd is None else cwd
    cp = subprocess.run(cmd, cwd=str(run_cwd), capture_output=True, text=True)
    return int(cp.returncode), cp.stdout, cp.stderr


def _collect_error_lines(stderr_text: str) -> list[str]:
    out: list[str] = []
    for raw in stderr_text.splitlines():
        if "error CS" in raw:
            out.append(raw.strip())
    return out


def _summarize_errors(error_lines: list[str]) -> tuple[Counter[str], Counter[str]]:
    code_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for line in error_lines:
        m = re.search(r"error\s+(CS\d+)", line)
        if m is not None:
            code_counts[m.group(1)] += 1

        if "Unexpected symbol `{" in line:
            category_counts["template_or_placeholder_fragment"] += 1
        if "local variable named" in line:
            category_counts["shadowed_local"] += 1
        if "expecting `;'" in line and "Unexpected symbol `)'" in line:
            category_counts["call_signature_shape"] += 1
        if "Unexpected symbol `" in line and ".`" in line:
            category_counts["invalid_member_chain"] += 1
    return code_counts, category_counts


def _render_report(
    out_path: Path,
    *,
    transpile_rc: int,
    transpile_msg: str,
    compile_rc: int,
    compile_msg: str,
    code_counts: Counter[str],
    category_counts: Counter[str],
    top_errors: list[str],
) -> None:
    today = _dt.date.today().isoformat()
    lines: list[str] = []
    lines.append("# P4 C# Single-Source Selfhost Compile Status")
    lines.append("")
    lines.append(f"計測日: {today}")
    lines.append("")
    lines.append("実行コマンド:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 tools/check_cs_single_source_selfhost_compile.py")
    lines.append("```")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- prepare: `python3 tools/prepare_selfhost_source_cs.py`")
    lines.append(f"- transpile selfhost source: `rc={transpile_rc}`")
    if transpile_msg != "":
        lines.append(f"- transpile note: `{transpile_msg}`")
    lines.append(f"- mcs compile: `rc={compile_rc}`")
    if compile_msg != "":
        lines.append(f"- compile note: `{compile_msg}`")
    lines.append("")
    lines.append("## Error Code Counts")
    lines.append("")
    lines.append("| code | count |")
    lines.append("|---|---:|")
    if len(code_counts) == 0:
        lines.append("| (none) | 0 |")
    else:
        for code, count in sorted(code_counts.items()):
            lines.append(f"| {code} | {count} |")
    lines.append("")
    lines.append("## Heuristic Categories")
    lines.append("")
    lines.append("| category | count |")
    lines.append("|---|---:|")
    if len(category_counts) == 0:
        lines.append("| (none) | 0 |")
    else:
        for cat, count in sorted(category_counts.items()):
            lines.append(f"| {cat} | {count} |")
    lines.append("")
    lines.append("## Top Errors (first 20)")
    lines.append("")
    if len(top_errors) == 0:
        lines.append("- (none)")
    else:
        for line in top_errors:
            lines.append("- " + line.replace("|", "/"))
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="check C# single-source selfhost compile status")
    ap.add_argument(
        "--out",
        default="docs-ja/plans/p4-cs-single-source-selfhost-compile-status.md",
        help="write markdown report to this path",
    )
    args = ap.parse_args()

    rc_prepare, out_prepare, err_prepare = _run(["python3", str(PREPARE)])
    if rc_prepare != 0:
        msg = (err_prepare.strip() or out_prepare.strip() or f"exit={rc_prepare}")
        _render_report(
            ROOT / args.out,
            transpile_rc=1,
            transpile_msg="prepare failed",
            compile_rc=1,
            compile_msg=msg,
            code_counts=Counter(),
            category_counts=Counter(),
            top_errors=[msg],
        )
        print(f"[FAIL] prepare failed: {msg}")
        return 1

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        stage1_cs = tmp / "cs_selfhost_full_stage1.cs"
        stage1_exe = tmp / "cs_selfhost_full_stage1.exe"
        rc_transpile, _, err_transpile = _run(["python3", str(PY2CS), str(SELFHOST_PY2CS), "-o", str(stage1_cs)])
        transpile_msg = err_transpile.strip()

        code_counts: Counter[str] = Counter()
        category_counts: Counter[str] = Counter()
        top_errors: list[str] = []
        compile_msg = ""
        rc_compile = 1

        if rc_transpile == 0 and stage1_cs.exists():
            cmd = ["mcs", "-langversion:latest", "-warn:0", "-out:" + str(stage1_exe), str(stage1_cs)]
            for runtime_file in RUNTIME_FILES:
                cmd.append(str(runtime_file))
            rc_compile, _, err_compile = _run(cmd)
            compile_msg = err_compile.strip().splitlines()[-1] if err_compile.strip() != "" else ""
            error_lines = _collect_error_lines(err_compile)
            code_counts, category_counts = _summarize_errors(error_lines)
            top_errors = error_lines[:20]
        else:
            if transpile_msg == "":
                transpile_msg = "stage1 cs output missing"
            compile_msg = "skipped (transpile failed)"

        _render_report(
            ROOT / args.out,
            transpile_rc=rc_transpile,
            transpile_msg=transpile_msg,
            compile_rc=rc_compile,
            compile_msg=compile_msg,
            code_counts=code_counts,
            category_counts=category_counts,
            top_errors=top_errors,
        )

    print(f"[OK] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

