#!/usr/bin/env python3
"""Build a hosted emitter and compare its output with the Python emitter.

Example:
    python3 tools/run/run_emitter_host_parity.py --host-lang go --hosted-emitter cpp
"""
from __future__ import annotations

import argparse
import datetime
import filecmp
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "tools" / "check") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "check"))

from runtime_parity_shared import Target, _tool_env_for_target, build_emitted_target_artifact, find_case_path  # type: ignore
from toolchain.misc.target_profiles import get_target_profile  # type: ignore

PARITY_DIR = ROOT / ".parity-results"


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _host_target(host_lang: str) -> str:
    return "ps1" if host_lang == "powershell" else host_lang


def _host_key(host_lang: str) -> str:
    return "powershell" if host_lang == "ps1" else host_lang


def _emitter_module(hosted_emitter: str) -> str:
    if hosted_emitter == "powershell":
        return "powershell"
    if hosted_emitter == "ps1":
        return "powershell"
    return hosted_emitter


def _emitter_cli_path(hosted_emitter: str) -> Path:
    module = _emitter_module(hosted_emitter)
    return ROOT / "src" / "toolchain" / "emit" / module / "cli.py"


def _entry_stem(hosted_emitter: str) -> str:
    return "toolchain_emit_" + _emitter_module(hosted_emitter).replace("-", "_") + "_cli"


def _run(cmd: list[str], *, cwd: Path, timeout_sec: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            env=proc_env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", exc.stderr or "timeout")


def _copy_linked_manifest(case_path: Path, hosted_emitter: str, work_dir: Path, timeout_sec: int) -> tuple[Path | None, str]:
    seed_out = work_dir / "seed_emit"
    if seed_out.exists():
        shutil.rmtree(seed_out)
    build_target = "ps1" if hosted_emitter in ("powershell", "ps1") else hosted_emitter
    result = _run(
        [
            sys.executable,
            str(ROOT / "src" / "pytra-cli.py"),
            "-build",
            str(case_path),
            "--target",
            build_target,
            "-o",
            str(seed_out),
        ],
        cwd=ROOT,
        timeout_sec=timeout_sec,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout or "").strip()

    generated_linked = ROOT / "work" / "tmp" / ("build_" + case_path.stem) / "linked"
    if not (generated_linked / "manifest.json").exists():
        return None, "linked manifest was not generated: " + str(generated_linked / "manifest.json")

    linked = work_dir / "linked"
    if linked.exists():
        shutil.rmtree(linked)
    shutil.copytree(generated_linked, linked)
    return linked / "manifest.json", ""


def _run_python_emitter(hosted_emitter: str, manifest_path: Path, out_dir: Path, timeout_sec: int) -> tuple[bool, str]:
    module = _emitter_module(hosted_emitter)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = _run(
        [
            sys.executable,
            "-m",
            "toolchain.emit." + module + ".cli",
            str(manifest_path),
            "--output-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        timeout_sec=timeout_sec,
        env={"PYTHONPATH": str(ROOT / "src")},
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip()
    return True, ""


def _run_hosted_emitter(runner: Path, manifest_path: Path, out_dir: Path, timeout_sec: int) -> tuple[bool, str]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = _run(
        [str(runner), str(manifest_path), "--output-dir", str(out_dir)],
        cwd=ROOT,
        timeout_sec=timeout_sec,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "").strip()
    return True, ""


def _dirs_match(left: Path, right: Path) -> tuple[bool, str]:
    cmp = filecmp.dircmp(left, right)
    diffs: list[str] = []

    def walk(node: filecmp.dircmp, prefix: str) -> None:
        for name in node.left_only:
            diffs.append(prefix + name + " only in python")
        for name in node.right_only:
            diffs.append(prefix + name + " only in hosted")
        for name in node.diff_files:
            diffs.append(prefix + name + " differs")
        for sub_name, sub_cmp in node.subdirs.items():
            walk(sub_cmp, prefix + sub_name + "/")

    walk(cmp, "")
    if diffs:
        return False, "; ".join(diffs[:10])
    return True, ""


def _load_emitter_host_doc(host_lang: str) -> dict[str, object]:
    path = PARITY_DIR / ("emitter_host_" + host_lang + ".json")
    if not path.exists():
        return {"host_lang": host_lang, "emitters": {}}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"host_lang": host_lang, "emitters": {}}
    if not isinstance(doc, dict):
        return {"host_lang": host_lang, "emitters": {}}
    emitters = doc.get("emitters")
    if not isinstance(emitters, dict):
        emitters = {}
        old_hosted = doc.get("hosted_emitter")
        if isinstance(old_hosted, str) and old_hosted != "":
            emitters[old_hosted] = {
                "build_status": doc.get("build_status", "not_tested"),
                "parity_status": doc.get("parity_status", "not_tested"),
                "parity_fixture_pass": doc.get("parity_fixture_pass", 0),
                "parity_fixture_fail": doc.get("parity_fixture_fail", 0),
                "timestamp": doc.get("timestamp", ""),
                "detail": doc.get("detail", ""),
            }
    return {"host_lang": host_lang, "emitters": emitters}


def _write_result(host_lang: str, hosted_emitter: str, entry: dict[str, object]) -> None:
    PARITY_DIR.mkdir(parents=True, exist_ok=True)
    host_key = _host_key(host_lang)
    doc = _load_emitter_host_doc(host_key)
    emitters = doc.get("emitters")
    if not isinstance(emitters, dict):
        emitters = {}
    emitters[hosted_emitter] = entry
    doc["host_lang"] = host_key
    doc["emitters"] = emitters
    out_path = PARITY_DIR / ("emitter_host_" + host_key + ".json")
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[INFO] wrote " + str(out_path.relative_to(ROOT)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run emitter host parity")
    parser.add_argument("--host-lang", required=True)
    parser.add_argument("--hosted-emitter", default="cpp")
    parser.add_argument("--case-root", default="fixture", choices=("fixture", "sample", "stdlib"))
    parser.add_argument("--case-stem", default="add")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--timeout-sec", type=int, default=180)
    args = parser.parse_args()

    host_lang = _host_key(args.host_lang.strip())
    host_target = _host_target(host_lang)
    hosted_emitter = _host_target(args.hosted_emitter.strip())
    now = _now()
    host_env: dict[str, str] | None = None
    try:
        profile = get_target_profile(host_target)
        host_env = _tool_env_for_target(Target(host_target, "", "", profile.runner_needs))
    except Exception:
        host_env = None

    emitter_cli = _emitter_cli_path(hosted_emitter)
    if not emitter_cli.exists():
        entry = {
            "build_status": "fail",
            "parity_status": "not_tested",
            "timestamp": now,
            "detail": "missing hosted emitter CLI: " + str(emitter_cli.relative_to(ROOT)),
        }
        _write_result(host_lang, hosted_emitter, entry)
        return 1

    work_dir = ROOT / "work" / "selfhost" / "emitter-host" / (host_lang + "_" + hosted_emitter)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    emit_dir = work_dir / "host_emit"
    build = _run(
        [
            sys.executable,
            str(ROOT / "src" / "pytra-cli.py"),
            "-build",
            str(emitter_cli),
            "--target",
            host_target,
            "-o",
            str(emit_dir),
        ],
        cwd=ROOT,
        timeout_sec=args.timeout_sec,
    )
    if build.returncode != 0:
        detail = (build.stderr or build.stdout or "").strip()
        _write_result(host_lang, hosted_emitter, {
            "build_status": "fail",
            "parity_status": "not_tested",
            "timestamp": now,
            "detail": detail[:1000],
        })
        return 1

    runner = work_dir / ("hosted_" + hosted_emitter + "_emitter")
    artifact = build_emitted_target_artifact(
        host_target,
        emit_dir,
        runner,
        entry_stem=_entry_stem(hosted_emitter),
        work_dir=work_dir,
        env=host_env,
        timeout_sec=args.timeout_sec,
    )
    if artifact.returncode != 0:
        detail = (artifact.stderr or artifact.stdout or "").strip()
        _write_result(host_lang, hosted_emitter, {
            "build_status": "fail",
            "parity_status": "not_tested",
            "timestamp": now,
            "detail": detail[:1000],
        })
        return 1

    manifest_path: Path
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = ROOT / manifest_path
    else:
        case_path = find_case_path(args.case_stem, args.case_root)
        if case_path is None:
            _write_result(host_lang, hosted_emitter, {
                "build_status": "ok",
                "parity_status": "fail",
                "timestamp": now,
                "detail": "case not found: " + args.case_root + "/" + args.case_stem,
            })
            return 1
        manifest_path, err = _copy_linked_manifest(case_path, hosted_emitter, work_dir, args.timeout_sec)
        if manifest_path is None:
            _write_result(host_lang, hosted_emitter, {
                "build_status": "ok",
                "parity_status": "fail",
                "timestamp": now,
                "detail": err[:1000],
            })
            return 1

    python_out = work_dir / "python"
    hosted_out = work_dir / "hosted"
    ok, err = _run_python_emitter(hosted_emitter, manifest_path, python_out, args.timeout_sec)
    if not ok:
        _write_result(host_lang, hosted_emitter, {
            "build_status": "ok",
            "parity_status": "fail",
            "timestamp": now,
            "detail": ("python emitter failed: " + err)[:1000],
        })
        return 1

    ok, err = _run_hosted_emitter(runner, manifest_path, hosted_out, args.timeout_sec)
    if not ok:
        _write_result(host_lang, hosted_emitter, {
            "build_status": "ok",
            "parity_status": "fail",
            "timestamp": now,
            "detail": ("hosted emitter failed: " + err)[:1000],
        })
        return 1

    match, detail = _dirs_match(python_out, hosted_out)
    entry = {
        "build_status": "ok",
        "parity_status": "ok" if match else "fail",
        "parity_fixture_pass": 1 if match else 0,
        "parity_fixture_fail": 0 if match else 1,
        "timestamp": _now(),
        "detail": detail if detail else "matched " + str(manifest_path.relative_to(ROOT)),
    }
    _write_result(host_lang, hosted_emitter, entry)
    if not match:
        print("[FAIL] output mismatch: " + detail)
        return 1
    print("[OK] " + host_lang + " hosted " + hosted_emitter + " emitter parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
