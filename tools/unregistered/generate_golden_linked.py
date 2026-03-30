#!/usr/bin/env python3
"""golden file 生成ツール (linked stage): east3-opt → linked manifest + east3.

toolchain2/link/ を使って linked golden files を生成する。

使い方:
  # fixture
  python3 tools/generate_golden_linked.py --case-root=fixture

  # sample
  python3 tools/generate_golden_linked.py --case-root=sample

  # 両方
  python3 tools/generate_golden_linked.py --case-root=fixture
  python3 tools/generate_golden_linked.py --case-root=sample

出力先:
  fixture: test/fixture/linked/<category>/<name>/manifest.json + east3/
  sample:  test/sample/linked/<name>/manifest.json + east3/
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# toolchain2 を import するために src を path に追加
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))


def _collect_east3_opt_files(east3_opt_dir: Path) -> list[tuple[Path, str]]:
    """Collect east3-opt files and return (path, relative_stem) pairs."""
    files: list[tuple[Path, str]] = []
    for f in sorted(east3_opt_dir.rglob("*.east3")):
        rel = f.relative_to(east3_opt_dir)
        stem = str(rel.with_suffix(""))  # "collections/add" or "01_mandelbrot"
        files.append((f, stem))
    return files


def _generate_linked(input_path: Path) -> dict[str, object]:
    """Link a single east3-opt file and return the manifest dict."""
    from toolchain2.link.linker import link_modules

    result = link_modules([str(input_path)], target="cpp", dispatch_mode="native")
    return result.manifest, result.linked_modules


def main() -> int:
    case_root = "sample"
    output_dir_text = ""

    i = 0
    args = sys.argv[1:]
    while i < len(args):
        tok = args[i]
        if tok == "--case-root" or tok.startswith("--case-root="):
            if "=" in tok:
                case_root = tok.split("=", 1)[1]
            else:
                if i + 1 >= len(args):
                    print(f"error: missing value for {tok}", file=sys.stderr)
                    return 1
                case_root = args[i + 1]
                i += 1
            i += 1
            continue
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print(f"error: missing value for {tok}", file=sys.stderr)
                return 1
            output_dir_text = args[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: generate_golden_linked.py [--case-root=sample|fixture] [-o DIR]")
            return 0
        i += 1

    if case_root == "fixture":
        east3_opt_dir = Path("test/fixture/east3-opt")
        default_output = "test/fixture/linked"
    elif case_root == "sample":
        east3_opt_dir = Path("test/sample/east3-opt")
        default_output = "test/sample/linked"
    else:
        print(f"error: unknown case-root: {case_root}", file=sys.stderr)
        return 1

    if output_dir_text == "":
        output_dir_text = default_output
    output_dir = Path(output_dir_text)

    files = _collect_east3_opt_files(east3_opt_dir)
    if len(files) == 0:
        print(f"error: no .east3 files found in {east3_opt_dir}", file=sys.stderr)
        return 1

    print(f"linked golden: case_root={case_root}, files={len(files)}, output={output_dir}")
    ok_count = 0
    fail_count = 0

    for src_path, rel_stem in files:
        case_dir = output_dir / rel_stem
        case_dir.mkdir(parents=True, exist_ok=True)
        try:
            manifest, linked_modules = _generate_linked(src_path)

            # Write manifest.json
            manifest_path = case_dir / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )

            # Write linked east3 files
            for mod in linked_modules:
                rel_path = mod.module_id.replace(".", "/") + ".east3.json"
                out_path = case_dir / "east3" / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(
                    json.dumps(mod.east_doc, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8",
                )

            print(f"  ok: {case_dir} ({len(linked_modules)} modules)")
            ok_count += 1
        except Exception as e:
            print(f"  FAIL: {src_path}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            fail_count += 1

    print(f"linked golden: {ok_count} ok, {fail_count} failed")
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
