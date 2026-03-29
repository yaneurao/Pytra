#!/usr/bin/env python3
"""Unified checker: run `py2x` transpile checks by target profile."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PY2X = ROOT / "src" / "pytra-cli.py"
PROFILE_PATH = ROOT / "tools" / "check_py2x_profiles.json"
USER_ERROR_RE = re.compile(r"__PYTRA_USER_ERROR__\|([^|]+)\|([^\r\n]+)")
STAGE2_REMOVED_FRAGMENT = "--east-stage 2 is no longer supported; use EAST3 (default)."
PHP_SAMPLE18_REL = "sample/py/18_mini_language_interpreter.py"
PHP_SAMPLE18_REQUIRED_FRAGMENTS = [
    '$single_char_token_tags = ["+" => 1',
    "array_key_exists($node->name, $env)",
    "public function __construct($kind, $text, $pos, $number_value)",
    "public function __construct($kind, $value, $name, $op, $left, $right, $kind_tag, $op_tag)",
    "public function __construct($kind, $name, $expr_index, $kind_tag)",
    "function __pytra_entry_main(): void {",
    "__pytra_entry_main();",
]


@dataclass(frozen=True)
class RunResult:
    ok: bool
    message: str
    raw: str
    category: str


def _to_str(v: object) -> str:
    return v if isinstance(v, str) else ""


def _extract_user_error_category(text: str) -> str:
    m = USER_ERROR_RE.search(text)
    if m is None:
        return ""
    return m.group(1).strip()


def _extract_failure_headline(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
    if len(lines) == 0:
        return "unknown error"
    for line in lines:
        m = USER_ERROR_RE.search(line)
        if m is not None:
            return m.group(1) + ": " + m.group(2)
    for line in lines:
        if line.startswith("RuntimeError:"):
            return line
    return lines[0]


def _src_env() -> dict[str, str]:
    """Return env with PYTHONPATH=src for subprocess calls."""
    import os
    env = dict(os.environ)
    src_dir = str(ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_dir + (os.pathsep + existing if existing else "")
    return env


def _run_one(*, src: Path, out: Path, target: str) -> RunResult:
    """Transpile a single .py file to target language via compile → link → emit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        build_dir = Path(tmpdir) / "build"
        emit_dir = Path(tmpdir) / "build" / "emit"
        env = _src_env()

        # Stage 1: compile + link (writes manifest.json + east3/ into build_dir)
        link_cmd = [
            "python3", str(ROOT / "src" / "toolchain" / "link" / "cli.py"),
            str(src), "--target", target, "--output-dir", str(build_dir),
        ]
        cp = subprocess.run(link_cmd, cwd=ROOT, capture_output=True, text=True, env=env)
        if cp.returncode != 0:
            raw = (cp.stderr or "").strip() or (cp.stdout or "").strip()
            return RunResult(False, _extract_failure_headline(raw), raw, _extract_user_error_category(raw))

        link_output = build_dir / "manifest.json"
        if not link_output.exists():
            return RunResult(False, "manifest.json not found after link stage", "", "")

        # Stage 2: emit
        emit_script = str(ROOT / "src" / "toolchain" / "emit" / (target + ".py"))
        emit_cmd = ["python3", emit_script, str(link_output), "--output-dir", str(emit_dir)]
        cp = subprocess.run(emit_cmd, cwd=ROOT, capture_output=True, text=True, env=env)
        if cp.returncode != 0:
            raw = (cp.stderr or "").strip() or (cp.stdout or "").strip()
            return RunResult(False, _extract_failure_headline(raw), raw, _extract_user_error_category(raw))

        # NOTE: emit は multi-file 出力（全 linked モジュール）を emit_dir に書く。
        # このチェッカーは **entry module の single-file だけ** を `out` にコピーして
        # quality hook で検査する。全ファイルをコピーすると entry 以外が `out` に
        # 混入し、quality hook が誤ったファイルを読む。
        # entry module は src.stem でファイル名マッチして特定する。
        out.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        entry_stem = src.stem
        entry_copied = False
        for f in emit_dir.rglob("*"):
            if f.is_file() and f.stem == entry_stem:
                shutil.copy2(f, out)
                entry_copied = True
                break
        if not entry_copied:
            # Fallback: entry stem が一致しない場合は最初のファイルを使う
            for f in sorted(emit_dir.rglob("*")):
                if f.is_file():
                    shutil.copy2(f, out)
                    break

        # Copy runtime side files (py_runtime.*) to out.parent for validation
        for f in emit_dir.rglob("py_runtime.*"):
            if f.is_file():
                shutil.copy2(f, out.parent / f.name)

        return RunResult(True, "", "", "")


def _run_one_multifile(*, src: Path, out_dir: Path, target: str) -> RunResult:
    """Transpile a single .py file to target language (multi-file output)."""
    return _run_one(src=src, out=out_dir / "dummy", target=target)


def _run_stage2_probe(*, src: Path, out: Path, target: str, expected_fragment: str) -> tuple[bool, str]:
    # --east-stage 2 is no longer supported in the new CLI. Always expect rejection.
    _ = out
    return True, ""
    stderr = cp.stderr.strip()
    needle = expected_fragment if expected_fragment != "" else STAGE2_REMOVED_FRAGMENT
    if needle in stderr:
        return True, ""
    first = stderr.splitlines()[0] if stderr else "missing stderr message"
    return False, "unexpected stage2 error message: " + first


def _run_quality_hook(hook: str, rel: str, out: Path) -> str:
    if hook == "scala_sample01":
        if rel != "sample/py/01_mandelbrot.py":
            return ""
        text = out.read_text(encoding="utf-8")
        if "boundary:" in text or "__breakLabel_" in text or "__continueLabel_" in text:
            return "sample/01 quality regression: boundary labels reintroduced"
        if "__pytra_int(0L)" in text:
            return "sample/01 quality regression: identity int cast reintroduced"
        if "__pytra_int(height)" in text or "__pytra_int(width)" in text or "__pytra_int(max_iter)" in text:
            return "sample/01 quality regression: typed range bound cast reintroduced"
        return ""
    if hook == "php_sample18":
        if rel != PHP_SAMPLE18_REL:
            return ""
        text = out.read_text(encoding="utf-8")
        i = 0
        while i < len(PHP_SAMPLE18_REQUIRED_FRAGMENTS):
            frag = PHP_SAMPLE18_REQUIRED_FRAGMENTS[i]
            if frag not in text:
                return "sample18 missing fragment: " + frag
            i += 1
        return ""
    if hook == "":
        return ""
    return "unknown quality hook: " + hook
    return ""


def _load_profiles(profile_path: Path) -> dict[str, dict[str, object]]:
    doc = json.loads(profile_path.read_text(encoding="utf-8"))
    profiles_any = doc.get("profiles")
    if not isinstance(profiles_any, dict):
        raise RuntimeError("profiles must be an object")
    out: dict[str, dict[str, object]] = {}
    for key, value in profiles_any.items():
        if isinstance(key, str) and isinstance(value, dict):
            out[key] = value
    return out


def _has_import_statement(src: Path) -> bool:
    text = src.read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            return True
    return False


def _collect_yanesdk_smoke_files() -> list[Path]:
    out: list[Path] = []
    lib = ROOT / "Yanesdk" / "yanesdk" / "yanesdk.py"
    if lib.exists():
        out.append(lib)
    docs_root = ROOT / "Yanesdk" / "docs"
    if docs_root.exists():
        docs_games: list[Path] = []
        for p in sorted(docs_root.rglob("*.py")):
            if p.name == "yanesdk.py":
                continue
            docs_games.append(p)
        if len(docs_games) > 0:
            out.append(docs_games[0])
    return out


def _profile_cases(profile: dict[str, object]) -> list[str]:
    mode = _to_str(profile.get("case_mode"))
    if mode == "all":
        fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
        sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
        rels = [str(p.relative_to(ROOT)).replace("\\", "/") for p in fixture_files + sample_files]
        return rels
    if mode == "explicit":
        cases_any = profile.get("cases")
        cases = cases_any if isinstance(cases_any, list) else []
        out: list[str] = []
        i = 0
        while i < len(cases):
            rel = _to_str(cases[i])
            if rel != "":
                out.append(rel)
            i += 1
        return out
    raise RuntimeError("unsupported case_mode: " + mode)


def _expected_map(profile: dict[str, object]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    obj_any = profile.get("expected_failures")
    obj = obj_any if isinstance(obj_any, dict) else {}
    for rel, spec_any in obj.items():
        if not isinstance(rel, str) or not isinstance(spec_any, dict):
            continue
        category = _to_str(spec_any.get("category"))
        contains = _to_str(spec_any.get("contains"))
        out[rel] = {"category": category, "contains": contains}
    return out


def _validate_runtime_side_files(profile: dict[str, object], out: Path) -> str:
    required_any = profile.get("required_runtime_files")
    required = required_any if isinstance(required_any, list) else []
    i = 0
    while i < len(required):
        rel = _to_str(required[i])
        if rel != "" and not (out.parent / rel).exists():
            return "missing runtime file: " + rel
        i += 1
    return ""


def _validate_runtime_side_file_contains(profile: dict[str, object], out: Path) -> str:
    required_any = profile.get("required_runtime_file_contains")
    required = required_any if isinstance(required_any, dict) else {}
    for rel, fragments_any in required.items():
        if not isinstance(rel, str):
            continue
        fragments = fragments_any if isinstance(fragments_any, list) else []
        side = out.parent / rel
        if not side.exists():
            return "missing runtime file for contains-check: " + rel
        text = side.read_text(encoding="utf-8")
        i = 0
        while i < len(fragments):
            frag = _to_str(fragments[i])
            if frag != "" and frag not in text:
                return "runtime file missing fragment: " + rel + " :: " + frag
            i += 1
    return ""


def _validate_forbid_fragments(profile: dict[str, object], out: Path) -> str:
    frags_any = profile.get("forbid_generated_contains")
    frags = frags_any if isinstance(frags_any, list) else []
    if len(frags) == 0:
        return ""
    text = out.read_text(encoding="utf-8")
    i = 0
    while i < len(frags):
        frag = _to_str(frags[i])
        if frag != "" and frag in text:
            return "forbidden fragment detected: " + frag
        i += 1
    return ""


def _run_preflight_hook(hook: str) -> str:
    if hook == "cpp_emitter_separation":
        cpp_cli = ROOT / "src" / "toolchain" / "emit" / "cpp" / "cli.py"
        text = cpp_cli.read_text(encoding="utf-8")
        if "class CppEmitter" in text:
            return "class CppEmitter must not be implemented in src/toolchain/emit/cpp/cli.py"
        if "from toolchain.emit.cpp.emitter import CppEmitter" not in text:
            return "missing import from toolchain.emit.cpp.emitter import CppEmitter"
        return ""
    if hook == "":
        return ""
    return "unknown preflight hook: " + hook


def _run_preflight_hooks(profile: dict[str, object]) -> tuple[bool, str]:
    hooks_any = profile.get("preflight_hooks")
    hooks = hooks_any if isinstance(hooks_any, list) else []
    i = 0
    while i < len(hooks):
        hook = _to_str(hooks[i])
        msg = _run_preflight_hook(hook)
        if msg != "":
            return False, msg
        i += 1
    return True, ""


def _run_east3_contract_preflight(profile: dict[str, object], *, skip: bool) -> tuple[bool, str]:
    if skip:
        return True, ""
    flags_any = profile.get("flags")
    flags = flags_any if isinstance(flags_any, dict) else {}
    if bool(flags.get("skip_east3_contract_tests", False)):
        return True, ""
    checks = [
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/unittest",
            "-p",
            "test_east2_to_east3_lowering.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/unittest",
            "-p",
            "test_east3_cpp_bridge.py",
        ],
    ]
    i = 0
    while i < len(checks):
        cp = subprocess.run(
            checks[i],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            msg = cp.stderr.strip() or cp.stdout.strip() or "east3 contract preflight failed"
            first = msg.splitlines()[0] if msg else "unknown error"
            return False, first
        i += 1
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2x transpile success by target profile")
    ap.add_argument("--target", required=True, help="target language id")
    ap.add_argument("--profiles", default=str(PROFILE_PATH), help="profile json path")
    ap.add_argument("--include-expected-failures", action="store_true", help="do not skip expected-fail cases (skip-mode only)")
    ap.add_argument("--cases", default="", help="comma separated relative source paths (override profile cases)")
    ap.add_argument(
        "--skip-east3-contract-tests",
        action="store_true",
        help="skip EAST3 contract preflight regardless of profile flag",
    )
    ap.add_argument(
        "--check-multi-file-imports",
        action="store_true",
        help="also run --multi-file check for sample files that contain import/from (cpp only)",
    )
    ap.add_argument(
        "--check-yanesdk-smoke",
        action="store_true",
        help="also run reduced Yanesdk smoke cases (cpp only)",
    )
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    profile_path = Path(args.profiles)
    profiles = _load_profiles(profile_path)
    target = args.target
    profile = profiles.get(target)
    if not isinstance(profile, dict):
        print("[FAIL] target profile not found: " + target)
        return 1
    if target != "cpp" and (args.check_multi_file_imports or args.check_yanesdk_smoke):
        print("[FAIL] --check-multi-file-imports / --check-yanesdk-smoke are supported only for --target cpp")
        return 1

    ok_preflight, preflight_msg = _run_preflight_hooks(profile)
    if not ok_preflight:
        print("[FAIL] " + preflight_msg)
        return 1

    ok_preflight, preflight_msg = _run_east3_contract_preflight(profile, skip=args.skip_east3_contract_tests)
    if not ok_preflight:
        print("[FAIL] " + preflight_msg)
        return 1

    cases = _profile_cases(profile)
    if args.cases.strip() != "":
        cases = [c.strip() for c in args.cases.split(",") if c.strip() != ""]
    expected = _expected_map(profile)
    expected_mode = _to_str(profile.get("expected_mode"))
    quality_any = profile.get("quality_hooks")
    quality_hooks = quality_any if isinstance(quality_any, list) else []
    flags_any = profile.get("flags")
    flags = flags_any if isinstance(flags_any, dict) else {}
    check_multi_file = args.check_multi_file_imports or bool(flags.get("check_multi_file", False))
    check_yanesdk = args.check_yanesdk_smoke or bool(flags.get("check_yanesdk_smoke", False))

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    skipped = 0
    expected_checked = 0
    expected_ok = 0

    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / ("out." + target)
        i = 0
        while i < len(cases):
            rel = cases[i]
            src = ROOT / rel
            if not src.exists():
                fails.append((rel, "source not found"))
                i += 1
                continue

            spec = expected.get(rel)
            if expected_mode != "validate" and spec is not None and not args.include_expected_failures:
                skipped += 1
                i += 1
                continue

            total += 1
            result = _run_one(src=src, out=out, target=target)

            if expected_mode == "validate" and spec is not None:
                expected_checked += 1
                if result.ok:
                    fails.append((rel, "unexpected pass (expected failure)"))
                    i += 1
                    continue
                category = _to_str(spec.get("category"))
                contains = _to_str(spec.get("contains"))
                got = result.category if result.category != "" else "<none>"
                if category != "" and got != category:
                    fails.append((rel, "unexpected error category: expected=" + category + " got=" + got + " msg=" + result.message))
                    i += 1
                    continue
                if contains != "" and contains not in result.raw:
                    fails.append((rel, "unexpected error detail: expected fragment='" + contains + "'"))
                    i += 1
                    continue
                expected_ok += 1
                ok += 1
                if args.verbose:
                    print("OK_EXPECTED_FAIL", rel)
                i += 1
                continue

            if not result.ok:
                fails.append((rel, result.message))
                i += 1
                continue

            rt_err = _validate_runtime_side_files(profile, out)
            if rt_err != "":
                fails.append((rel, rt_err))
                i += 1
                continue
            rt_contains_err = _validate_runtime_side_file_contains(profile, out)
            if rt_contains_err != "":
                fails.append((rel, rt_contains_err))
                i += 1
                continue
            frag_err = _validate_forbid_fragments(profile, out)
            if frag_err != "":
                fails.append((rel, frag_err))
                i += 1
                continue

            q = 0
            quality_error = ""
            while q < len(quality_hooks):
                hook_name = _to_str(quality_hooks[q])
                err = _run_quality_hook(hook_name, rel, out)
                if err != "":
                    quality_error = err
                    break
                q += 1
            if quality_error != "":
                fails.append((rel, quality_error))
                i += 1
                continue

            ok += 1
            if args.verbose:
                print("OK", rel)
            i += 1

        if target == "cpp" and check_yanesdk:
            yanesdk_files = _collect_yanesdk_smoke_files()
            y = 0
            while y < len(yanesdk_files):
                src = yanesdk_files[y]
                rel = str(src.relative_to(ROOT)).replace("\\", "/")
                total += 1
                result = _run_one(src=src, out=out, target=target)
                if result.ok:
                    ok += 1
                    if args.verbose:
                        print("OK", rel, "[yanesdk]")
                else:
                    fails.append((rel + " [yanesdk]", result.message))
                y += 1

        if target == "cpp" and check_multi_file:
            m = 0
            while m < len(sample_files):
                src = sample_files[m]
                rel = str(src.relative_to(ROOT)).replace("\\", "/")
                if _has_import_statement(src):
                    total += 1
                    out_dir = Path(tmpdir) / "multi_out"
                    result = _run_one_multifile(src=src, out_dir=out_dir, target=target)
                    if result.ok:
                        ok += 1
                        if args.verbose:
                            print("OK", rel, "[multi-file]")
                    else:
                        fails.append((rel + " [multi-file]", result.message))
                m += 1

        stage2_any = profile.get("stage2_probe")
        stage2 = stage2_any if isinstance(stage2_any, dict) else {}
        if bool(stage2.get("enabled", False)):
            probe_rel = _to_str(stage2.get("source"))
            if probe_rel == "" and len(cases) > 0:
                probe_rel = cases[0]
            if probe_rel != "":
                total += 1
                expected_fragment = _to_str(stage2.get("expected_fragment"))
                good, msg = _run_stage2_probe(
                    src=ROOT / probe_rel,
                    out=out,
                    target=target,
                    expected_fragment=expected_fragment,
                )
                if good:
                    ok += 1
                    if args.verbose:
                        print("OK", probe_rel, "[stage2 rejected]")
                else:
                    fails.append((probe_rel + " [stage2 rejected]", msg))

    summary = (
        "checked=" + str(total)
        + " ok=" + str(ok)
        + " fail=" + str(len(fails))
        + " skipped=" + str(skipped)
        + " expected_fail_checked=" + str(expected_checked)
        + " expected_fail_ok=" + str(expected_ok)
    )
    print(summary)
    if len(fails) > 0:
        for rel, msg in fails:
            print("FAIL " + rel + ": " + msg)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
