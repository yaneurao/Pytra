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


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    run_cwd = ROOT if cwd is None else cwd
    cp = subprocess.run(cmd, cwd=str(run_cwd), capture_output=True, text=True)
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


def _copy_js_runtime(stage2_src_root: Path) -> None:
    src_runtime = ROOT / "src" / "runtime" / "js"
    dst_runtime = stage2_src_root / "runtime" / "js"
    shutil.copytree(src_runtime, dst_runtime, dirs_exist_ok=True)


def _prepare_js_stage2_tree(stage2_root: Path, entry_py: Path) -> tuple[bool, str, Path]:
    stage2_src_root = stage2_root / "src"
    stage2_src_root.mkdir(parents=True, exist_ok=True)
    _copy_js_runtime(stage2_src_root)

    py2js_cli = ROOT / "src" / "py2js.py"
    repo_src_root = ROOT / "src"
    queue: list[Path] = [entry_py]
    emitted: set[str] = set()
    entry_js = stage2_src_root / entry_py.relative_to(repo_src_root).with_suffix(".js")

    while len(queue) > 0:
        py_src = queue.pop(0)
        try:
            rel_py = py_src.relative_to(repo_src_root)
        except ValueError:
            return False, "js stage2 prepare: source escaped repo src", entry_js
        rel_key = rel_py.as_posix()
        if rel_key in emitted:
            continue

        out_js = stage2_src_root / rel_py.with_suffix(".js")
        out_js.parent.mkdir(parents=True, exist_ok=True)
        ok_emit, msg_emit = _run(["python3", str(py2js_cli), str(py_src), "-o", str(out_js)])
        if not ok_emit:
            return False, "js stage2 emit failed at " + rel_key + ": " + msg_emit, entry_js
        emitted.add(rel_key)

        js_text = out_js.read_text(encoding="utf-8")
        import_paths = _extract_js_relative_imports(js_text)
        for rel_import in import_paths:
            resolved_js = (out_js.parent / rel_import).resolve()
            try:
                resolved_rel_js = resolved_js.relative_to(stage2_src_root.resolve())
            except ValueError:
                continue
            dep_py = (repo_src_root / resolved_rel_js).with_suffix(".py")
            if dep_py.exists():
                queue.append(dep_py)

    return True, "", entry_js


def _run_js_stage2(sample_py: Path, stage2_tmp_dir: Path, entry_py: Path) -> tuple[str, str]:
    has_node = shutil.which("node") is not None
    if not has_node:
        return "blocked", "node not found"

    js_root = stage2_tmp_dir / "js_stage2"
    ok_prepare, msg_prepare, entry_js = _prepare_js_stage2_tree(js_root, entry_py)
    if not ok_prepare:
        return "fail", msg_prepare

    out2 = js_root / "js_stage2_out.js"
    ok_run, msg_run = _run(["node", str(entry_js), str(sample_py), "-o", str(out2)], cwd=js_root)
    if ok_run and out2.exists():
        return "pass", "sample/py/01 transpile ok"
    if msg_run != "":
        return "fail", msg_run
    return "fail", "stage2 output missing"


def _run_rs_stage2(stage1_out: Path, sample_py: Path, stage2_tmp_dir: Path) -> tuple[str, str]:
    has_rustc = shutil.which("rustc") is not None
    if not has_rustc:
        return "blocked", "rustc not found"

    out_bin = stage2_tmp_dir / "py2rs_stage2.out"
    ok_build, msg_build = _run(["rustc", str(stage1_out), "-O", "-o", str(out_bin)])
    if not ok_build:
        return "fail", msg_build

    out2 = stage2_tmp_dir / "rs_stage2_out.rs"
    ok_run, msg_run = _run([str(out_bin), str(sample_py), "-o", str(out2)])
    if ok_run and out2.exists():
        return "pass", "sample/py/01 transpile ok"
    if msg_run != "":
        return "fail", msg_run
    return "fail", "stage2 output missing"


def _run_cs_stage2(stage1_out: Path, sample_py: Path, stage2_tmp_dir: Path) -> tuple[str, str]:
    has_mcs = shutil.which("mcs") is not None
    has_mono = shutil.which("mono") is not None
    if (not has_mcs) or (not has_mono):
        return "blocked", "mcs/mono not found"

    out_exe = stage2_tmp_dir / "py2cs_stage2.exe"
    runtime_files = [
        ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "py_runtime.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "time.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "math.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "png_helper.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "gif_helper.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "std" / "pathlib.cs",
    ]
    compile_cmd = ["mcs", "-warn:0", "-out:" + str(out_exe), str(stage1_out)]
    for runtime_file in runtime_files:
        compile_cmd.append(str(runtime_file))
    ok_build, msg_build = _run(compile_cmd)
    if not ok_build:
        return "fail", msg_build

    out2 = stage2_tmp_dir / "cs_stage2_out.cs"
    ok_run, msg_run = _run(["mono", str(out_exe), str(sample_py), "-o", str(out2)])
    if ok_run and out2.exists():
        return "pass", "sample/py/01 transpile ok"
    if msg_run != "":
        return "fail", msg_run
    return "fail", "stage2 output missing"


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
        default="docs/ja/plans/p1-multilang-selfhost-status.md",
        help="write markdown report to this path",
    )
    ap.add_argument(
        "--strict-stage1",
        action="store_true",
        help="return non-zero when any stage1 self-transpile fails",
    )
    args = ap.parse_args()

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
                stage2_status, stage2_note = _run_js_stage2(sample_py, tmp, src)
                rows.append(StatusRow(spec.lang, "pass", mode, stage2_status, stage2_note))
                continue

            if spec.lang == "rs":
                stage2_status, stage2_note = _run_rs_stage2(out1, sample_py, tmp)
                rows.append(StatusRow(spec.lang, "pass", mode, stage2_status, stage2_note))
                continue

            if spec.lang == "cs":
                stage2_status, stage2_note = _run_cs_stage2(out1, sample_py, tmp)
                rows.append(StatusRow(spec.lang, "pass", mode, stage2_status, stage2_note))
                continue

            rows.append(StatusRow(spec.lang, "pass", mode, "skip", "stage2 scope is rs/cs/js only"))

    out_path = ROOT / args.out
    _render_report(rows, out_path)
    print(f"[OK] wrote {args.out}")
    if args.strict_stage1 and stage1_fail > 0:
        print(f"[FAIL] stage1 failures={stage1_fail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
