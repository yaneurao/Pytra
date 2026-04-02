"""
gen_sample_benchmark.py  (P2-BENCH-S3)

.parity-results/*_sample.json を読み、sample-preview/README-ja.md と sample-preview/README.md の
「実行速度の比較」テーブルを自動更新する。

計測されていない言語/ケースは元の値をそのまま維持する（—に変えない）。
PyPy は parity check では計測しないため常に元の値を保持する。

使い方:
    python3 tools/gen/gen_sample_benchmark.py
    python3 tools/gen/gen_sample_benchmark.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARITY_DIR = ROOT / ".parity-results"

# README 上の列順（PyPy は parity check 非対象）
# target_key → (ja_col_header, en_col_header)
# None は PyPy（手動値保持）
COLUMNS: list[tuple[str | None, str, str]] = [
    ("python",  "Python",  "Python"),
    (None,      "PyPy",    "PyPy"),
    ("cpp",     "C++",     "C++"),
    ("rs",      "Rust",    "Rust"),
    ("cs",      "C#",      "C#"),
    ("ps1",     "PS",      "PS"),
    ("js",      "JS",      "JS"),
    ("ts",      "TS",      "TS"),
    ("dart",    "Dart",    "Dart"),
    ("go",      "Go",      "Go"),
    ("java",    "Java",    "Java"),
    ("swift",   "Swift",   "Swift"),
    ("kotlin",  "Kotlin",  "Kotlin"),
    ("ruby",    "Ruby",    "Ruby"),
    ("lua",     "Lua",     "Lua"),
    ("scala",   "Scala3",  "Scala3"),
    ("php",     "PHP",     "PHP"),
    ("nim",     "Nim",     "Nim"),
    ("julia",   "Julia",   "Julia"),
    ("zig",     "Zig",     "Zig"),
]

# case_stem prefix → (ja description, en description)
CASE_DESCS: dict[str, tuple[str, str]] = {
    "01": ("マンデルブロ集合（PNG）",              "Mandelbrot set (PNG)"),
    "02": ("球の簡易レイトレーサ（PNG）",           "Simple sphere ray tracer (PNG)"),
    "03": ("ジュリア集合（PNG）",                  "Julia set (PNG)"),
    "04": ("オービットトラップ Julia（PNG）",       "Orbit-trap Julia set (PNG)"),
    "05": ("マンデルブロズーム（GIF）",             "Mandelbrot zoom (GIF)"),
    "06": ("ジュリア集合パラメータ掃引（GIF）",     "Julia parameter sweep (GIF)"),
    "07": ("ライフゲーム（GIF）",                  "Game of Life (GIF)"),
    "08": ("ラングトンのアリ（GIF）",              "Langton's Ant (GIF)"),
    "09": ("炎シミュレーション（GIF）",             "Flame simulation (GIF)"),
    "10": ("プラズマエフェクト（GIF）",             "Plasma effect (GIF)"),
    "11": ("リサージュ粒子（GIF）",                "Lissajous particles (GIF)"),
    "12": ("ソート可視化（GIF）",                  "Sorting visualization (GIF)"),
    "13": ("迷路生成ステップ（GIF）",              "Maze generation steps (GIF)"),
    "14": ("簡易レイマーチング（GIF）",             "Simple ray marching (GIF)"),
    "15": ("波干渉ループ（GIF）",                  "Wave interference loop (GIF)"),
    "16": ("ガラス彫刻のカオス回転（GIF）",         "Chaos rotation of glass sculpture (GIF)"),
    "17": ("モンテカルロ法で円周率近似",            "Monte Carlo Pi approximation"),
    "18": ("ミニ言語インタプリタ",                  "Mini-language interpreter"),
}


def load_timing_data() -> dict[str, dict[str, float]]:
    """Return {case_prefix: {target: elapsed_sec}} from .parity-results/*_sample.json."""
    data: dict[str, dict[str, float]] = {}  # data["01"]["cpp"] = 0.79

    # Load each target's results
    for target_key, _, _ in COLUMNS:
        if target_key is None:
            continue
        jpath = PARITY_DIR / f"{target_key}_sample.json"
        if not jpath.exists():
            continue
        try:
            doc = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:
            continue
        results = doc.get("results", {})
        for case_stem, entry in results.items():
            if not isinstance(entry, dict):
                continue
            elapsed = entry.get("elapsed_sec")
            if not isinstance(elapsed, (int, float)):
                continue
            # case_stem is like "01_mandelbrot" — extract prefix
            prefix = case_stem.split("_")[0]
            if prefix not in data:
                data[prefix] = {}
            data[prefix][target_key] = float(elapsed)

    return data


def _fmt(val: float) -> str:
    """Format elapsed seconds for table cell."""
    return f"{val:.3f}"


def build_table_rows(
    existing_rows: dict[str, list[str]],
    timing: dict[str, dict[str, float]],
    lang: str,  # "ja" or "en"
) -> list[str]:
    """Build replacement table rows.

    existing_rows: {prefix: [col0, col1, ...]} parsed from the current README.
    timing: new measurements from parity results.
    lang: "ja" or "en"
    """
    target_keys = [t for t, _, _ in COLUMNS]
    rows: list[str] = []

    for prefix, (ja_desc, en_desc) in sorted(CASE_DESCS.items()):
        desc = ja_desc if lang == "ja" else en_desc
        existing = existing_rows.get(prefix, [])
        new_cells: list[str] = []

        for col_idx, (target_key, _, _) in enumerate(COLUMNS):
            # Keep existing value if available; overwrite only with new measurement
            old_val = existing[col_idx + 2] if len(existing) > col_idx + 2 else "—"

            if target_key is None:
                # PyPy — always keep old value
                new_cells.append(old_val)
            elif prefix in timing and target_key in timing[prefix]:
                new_cells.append(_fmt(timing[prefix][target_key]))
            else:
                new_cells.append(old_val)

        rows.append(f"|{prefix} |{desc}|" + "|".join(new_cells) + "|")

    return rows


def parse_existing_table(content: str) -> dict[str, list[str]]:
    """Parse existing benchmark table rows.
    Returns {prefix: [cells...]} where cells[0]=prefix, cells[1]=desc, cells[2..]=measurements.
    """
    result: dict[str, list[str]] = {}
    for line in content.splitlines():
        m = re.match(r"^\|(\d+)\s*\|(.+)$", line)
        if not m:
            continue
        prefix = m.group(1)
        rest = line.strip("|").split("|")
        result[prefix] = rest
    return result


def build_header(lang: str) -> tuple[str, str]:
    """Return (header_line, separator_line) for the benchmark table."""
    if lang == "ja":
        col_names = ["No.", "内容"] + [h for _, h, _ in COLUMNS]
    else:
        col_names = ["No.", "Workload"] + [h for _, _, h in COLUMNS]
    header = "|" + "|".join(col_names) + "|"
    sep = "|-|-" + "|-:" * len(COLUMNS) + "|"
    return header, sep


def replace_benchmark_section(content: str, timing: dict[str, dict[str, float]], lang: str) -> str:
    """Replace the benchmark table in README content.

    Finds the table between the header line and '### 計測条件' / '### Measurement Conditions'.
    """
    if lang == "ja":
        table_start_pat = re.compile(r"^\|No\.\|内容\|", re.MULTILINE)
        section_end_pat = re.compile(r"^### 計測条件", re.MULTILINE)
    else:
        table_start_pat = re.compile(r"^\|No\.\|Workload\|", re.MULTILINE)
        section_end_pat = re.compile(r"^### Measurement Conditions", re.MULTILINE)

    m_start = table_start_pat.search(content)
    m_end = section_end_pat.search(content)
    if not m_start or not m_end:
        return content  # no match — don't modify

    # Region to replace: from table header to section_end (exclusive)
    before = content[: m_start.start()]
    after = content[m_end.start():]

    # Parse existing table rows from region
    region = content[m_start.start(): m_end.start()]
    existing_rows = parse_existing_table(region)

    # Build new table
    header, sep = build_header(lang)
    rows = build_table_rows(existing_rows, timing, lang)

    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    note = f"> 最終自動更新: {now}" if lang == "ja" else f"> Last auto-updated: {now}"

    new_region = "\n".join([header, sep] + rows) + "\n\n" + note + "\n\n"
    return before + new_region + after


def update_readme(readme_path: Path, timing: dict[str, dict[str, float]], lang: str, dry_run: bool) -> None:
    content = readme_path.read_text(encoding="utf-8")
    updated = replace_benchmark_section(content, timing, lang)
    if updated == content:
        print(f"  (no change) {readme_path.relative_to(ROOT)}")
        return
    if dry_run:
        print(f"  [dry-run] would update {readme_path.relative_to(ROOT)}")
        return
    readme_path.write_text(updated, encoding="utf-8")
    print(f"  -> {readme_path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update sample benchmark table in README files")
    parser.add_argument("--dry-run", action="store_true", help="print what would change without writing")
    args = parser.parse_args()

    timing = load_timing_data()
    if not timing:
        print("[WARN] no timing data found in .parity-results/ — nothing to update")
        return 0

    measured = sum(len(v) for v in timing.values())
    print(f"[INFO] loaded timing for {len(timing)} cases, {measured} measurements total")

    # Write to sample-preview/ (git-ignored) instead of sample/ directly.
    # Copy the original README if not yet present in sample-preview/.
    preview_dir = ROOT / "sample-preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    for name in ("README-ja.md", "README.md"):
        preview = preview_dir / name
        if not preview.exists():
            original = ROOT / "sample" / name
            if original.exists():
                import shutil
                shutil.copy2(original, preview)
    lang_code = "ja"
    update_readme(preview_dir / "README-ja.md", timing, lang_code, args.dry_run)
    update_readme(preview_dir / "README.md",    timing, "en", args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
