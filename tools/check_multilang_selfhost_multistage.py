#!/usr/bin/env python3
"""Collect multistage selfhost status for non-C++ transpilers."""

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
    stage2: str
    stage3: str
    category: str
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


def _prepare_js_tree(stage_root: Path, entry_py: Path) -> tuple[bool, str, Path]:
    stage_src_root = stage_root / "src"
    stage_src_root.mkdir(parents=True, exist_ok=True)
    _copy_js_runtime(stage_src_root)

    py2js_cli = ROOT / "src" / "py2js.py"
    repo_src_root = ROOT / "src"
    queue: list[Path] = [entry_py]
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
        ok_emit, msg_emit = _run(["python3", str(py2js_cli), str(py_src), "-o", str(out_js)])
        if not ok_emit:
            return False, "js multistage emit failed at " + rel_key + ": " + msg_emit, entry_js
        emitted.add(rel_key)

        js_text = out_js.read_text(encoding="utf-8")
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

    return True, "", entry_js


def _run_js_multistage(stage_tmp: Path, src_py: Path, sample_py: Path) -> tuple[str, str, str, str]:
    if shutil.which("node") is None:
        return "blocked", "blocked", "toolchain_missing", "node not found"

    js_root = stage_tmp / "js_multistage"
    ok_prepare, msg_prepare, entry_js = _prepare_js_tree(js_root, src_py)
    if not ok_prepare:
        return "fail", "skip", "stage1_dependency_transpile_fail", msg_prepare

    stage2_src = js_root / "src" / "py2js_stage2.js"
    ok_stage2, msg_stage2 = _run(["node", str(entry_js), str(src_py), "-o", str(stage2_src)], cwd=js_root)
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"

    stage3_out = js_root / "js_stage3_sample.js"
    ok_stage3, msg_stage3 = _run(["node", str(stage2_src), str(sample_py), "-o", str(stage3_out)], cwd=js_root)
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
    ok_stage2, msg_stage2 = _run([str(stage1_bin), str(src_py), "-o", str(stage2_src)])
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"

    stage2_bin = stage_tmp / "py2rs_stage2.out"
    ok_build2, msg_build2 = _run(["rustc", str(stage2_src), "-O", "-o", str(stage2_bin)])
    if not ok_build2:
        return "pass", "fail", "stage2_compile_fail", msg_build2

    stage3_out = stage_tmp / "rs_stage3_sample.rs"
    ok_stage3, msg_stage3 = _run([str(stage2_bin), str(sample_py), "-o", str(stage3_out)])
    if not ok_stage3:
        return "pass", "fail", "sample_transpile_fail", msg_stage3
    if not stage3_out.exists():
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output missing"

    return "pass", "pass", "pass", "stage2/stage3 sample transpile ok"


def _cs_compile(src_cs: Path, out_exe: Path) -> tuple[bool, str]:
    runtime_files = [
        ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "py_runtime.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "built_in" / "time.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "png_helper.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "utils" / "gif_helper.cs",
        ROOT / "src" / "runtime" / "cs" / "pytra" / "std" / "pathlib.cs",
    ]
    compile_cmd = ["mcs", "-out:" + str(out_exe), str(src_cs)]
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

    stage2_src = stage_tmp / "py2cs_stage2.cs"
    ok_stage2, msg_stage2 = _run(["mono", str(stage1_exe), str(src_py), "-o", str(stage2_src)])
    if not ok_stage2:
        return "fail", "skip", "self_retranspile_fail", msg_stage2
    if not stage2_src.exists():
        return "fail", "skip", "self_retranspile_fail", "stage2 transpiler output missing"

    stage2_exe = stage_tmp / "py2cs_stage2.exe"
    ok_build2, msg_build2 = _cs_compile(stage2_src, stage2_exe)
    if not ok_build2:
        return "pass", "fail", "stage2_compile_fail", msg_build2

    stage3_out = stage_tmp / "cs_stage3_sample.cs"
    ok_stage3, msg_stage3 = _run(["mono", str(stage2_exe), str(sample_py), "-o", str(stage3_out)])
    if not ok_stage3:
        return "pass", "fail", "sample_transpile_fail", msg_stage3
    if not stage3_out.exists():
        return "pass", "fail", "sample_transpile_fail", "stage3 sample output missing"

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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="collect multistage selfhost status for non-cpp transpilers")
    ap.add_argument(
        "--out",
        default="docs-ja/plans/p1-multilang-selfhost-multistage-status.md",
        help="write markdown report to this path",
    )
    args = ap.parse_args()

    sample_py = ROOT / "sample" / "py" / "01_mandelbrot.py"
    rows: list[StatusRow] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for spec in LANGS:
            cli = ROOT / spec.cli
            src = ROOT / spec.src
            stage1_out = tmp / f"{spec.lang}_stage1{spec.ext}"

            ok_stage1, msg_stage1 = _run(["python3", str(cli), str(src), "-o", str(stage1_out)])
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

            rows.append(StatusRow(spec.lang, "pass", "skip", "skip", "runner_not_defined", "multistage runner is not defined"))

    out_path = ROOT / args.out
    _render_report(rows, out_path)
    print(f"[OK] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
