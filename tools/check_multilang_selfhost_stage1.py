#!/usr/bin/env python3
"""Collect stage1 selfhost status for non-C++ transpilers."""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class LangSpec:
    lang: str
    cli: str
    src: str
    ext: str


@dataclass
class StatusRow:
    lang: str
    stage1: str
    mode: str
    stage2: str
    note: str


LANGS: list[LangSpec] = [
    LangSpec("rs", "src/py2rs.py", "src/py2rs.py", ".rs"),
    LangSpec("cs", "src/py2cs.py", "src/py2cs.py", ".cs"),
    LangSpec("js", "src/py2js.py", "src/py2js.py", ".js"),
    LangSpec("ts", "src/py2ts.py", "src/py2ts.py", ".ts"),
    LangSpec("go", "src/py2go.py", "src/py2go.py", ".go"),
    LangSpec("java", "src/py2java.py", "src/py2java.py", ".java"),
    LangSpec("swift", "src/py2swift.py", "src/py2swift.py", ".swift"),
    LangSpec("kotlin", "src/py2kotlin.py", "src/py2kotlin.py", ".kt"),
]


def _run(cmd: list[str]) -> tuple[bool, str]:
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    if msg == "":
        msg = f"exit={cp.returncode}"
    parts = [ln.strip() for ln in msg.splitlines() if ln.strip() != ""]
    i = 0
    while i < len(parts):
        line = parts[i]
        if re.search(r"(Error|unsupported_|not_implemented|SyntaxError|TypeError|ReferenceError|RuntimeError|Exception)", line):
            return False, line
        i += 1
    if len(parts) > 0:
        return False, parts[-1]
    return False, msg


def _is_preview_output(text: str) -> bool:
    return ("プレビュー出力" in text) or ("TODO: 専用" in text) or ("preview backend" in text)


def _render_report(rows: list[StatusRow], out_path: Path) -> None:
    today = _dt.date.today().isoformat()
    lines: list[str] = []
    lines.append("# P1-MQ-04 Stage1 Status")
    lines.append("")
    lines.append(f"計測日: {today}")
    lines.append("")
    lines.append("実行コマンド:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 tools/check_multilang_selfhost_stage1.py")
    lines.append("```")
    lines.append("")
    lines.append("| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |")
    lines.append("|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| "
            + row.lang
            + " | "
            + row.stage1
            + " | "
            + row.mode
            + " | "
            + row.stage2
            + " | "
            + row.note.replace("|", "/")
            + " |"
        )
    lines.append("")
    lines.append("備考:")
    lines.append("- `stage1`: `src/py2<lang>.py` を同言語へ自己変換できるか。")
    lines.append("- `generated_mode`: 生成物が preview かどうか。")
    lines.append("- `stage2`: 生成された変換器で `sample/py/01_mandelbrot.py` を再変換できるか。")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="collect stage1 selfhost status for non-cpp transpilers")
    ap.add_argument(
        "--out",
        default="docs-ja/plans/p1-multilang-selfhost-status.md",
        help="write markdown report to this path",
    )
    ap.add_argument(
        "--strict-stage1",
        action="store_true",
        help="return non-zero when any stage1 self-transpile fails",
    )
    args = ap.parse_args()

    has_node = shutil.which("node") is not None
    sample_py = ROOT / "sample" / "py" / "01_mandelbrot.py"

    rows: list[StatusRow] = []
    stage1_fail = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for spec in LANGS:
            cli = ROOT / spec.cli
            src = ROOT / spec.src
            out1 = tmp / f"{spec.lang}_selfhost_stage1{spec.ext}"

            ok1, msg1 = _run(["python3", str(cli), str(src), "-o", str(out1)])
            if not ok1:
                rows.append(StatusRow(spec.lang, "fail", "unknown", "skip", msg1))
                stage1_fail += 1
                continue
            if not out1.exists():
                rows.append(StatusRow(spec.lang, "fail", "unknown", "skip", "stage1 output missing"))
                stage1_fail += 1
                continue

            txt = out1.read_text(encoding="utf-8")
            preview = _is_preview_output(txt)
            mode = "preview" if preview else "native"

            if preview:
                rows.append(StatusRow(spec.lang, "pass", mode, "blocked", "generated transpiler is preview-only"))
                continue

            if spec.lang == "js":
                if not has_node:
                    rows.append(StatusRow(spec.lang, "pass", mode, "skip", "node not found"))
                    continue
                out2 = tmp / "js_stage2_out.js"
                ok2, msg2 = _run(["node", str(out1), str(sample_py), "-o", str(out2)])
                if ok2 and out2.exists():
                    rows.append(StatusRow(spec.lang, "pass", mode, "pass", "sample/py/01 transpile ok"))
                else:
                    note = msg2 if msg2 != "" else "stage2 output missing"
                    rows.append(StatusRow(spec.lang, "pass", mode, "fail", note))
                continue

            rows.append(StatusRow(spec.lang, "pass", mode, "skip", "stage2 runner not automated"))

    out_path = ROOT / args.out
    _render_report(rows, out_path)
    print(f"[OK] wrote {args.out}")
    if args.strict_stage1 and stage1_fail > 0:
        print(f"[FAIL] stage1 failures={stage1_fail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
