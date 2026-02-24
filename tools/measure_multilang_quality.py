#!/usr/bin/env python3
"""Measure generated code quality signals across sample outputs."""

from __future__ import annotations

import argparse
import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class LangConfig:
    name: str
    rel_dir: str
    ext: str


@dataclass
class Metrics:
    files: int = 0
    lines: int = 0
    mut_count: int = 0
    paren_count: int = 0
    cast_count: int = 0
    clone_count: int = 0
    import_count: int = 0
    unused_import_est: int = 0


LANGS: list[LangConfig] = [
    LangConfig("cpp", "sample/cpp", ".cpp"),
    LangConfig("rs", "sample/rs", ".rs"),
    LangConfig("cs", "sample/cs", ".cs"),
    LangConfig("js", "sample/js", ".js"),
    LangConfig("ts", "sample/ts", ".ts"),
    LangConfig("go", "sample/go", ".go"),
    LangConfig("java", "sample/java", ".java"),
    LangConfig("swift", "sample/swift", ".swift"),
    LangConfig("kotlin", "sample/kotlin", ".kt"),
]


def _rate(count: int, lines: int) -> float:
    if lines <= 0:
        return 0.0
    return (float(count) * 1000.0) / float(lines)


def _cast_count(text: str, lang: str) -> int:
    if lang == "rs":
        return len(re.findall(r"\bas\s+[A-Za-z_][A-Za-z0-9_:<>\[\]]*", text))
    if lang == "cs":
        return len(
            re.findall(
                r"\((?:sbyte|byte|short|ushort|int|uint|long|ulong|float|double|decimal|char|bool|string|object)\)",
                text,
            )
        )
    if lang == "ts":
        return len(re.findall(r"\bas\s+[A-Za-z_][A-Za-z0-9_<>, \[\]\|&\?]*", text))
    if lang == "go":
        return len(re.findall(r"\b(?:int|int32|int64|float32|float64|string|byte|rune)\s*\(", text))
    if lang == "java":
        return len(re.findall(r"\((?:byte|short|int|long|float|double|boolean|char|String|Object)\)", text))
    if lang == "kotlin":
        return len(re.findall(r"\.(?:toInt|toLong|toFloat|toDouble|toString|toByte|toShort|toChar)\s*\(", text))
    if lang == "swift":
        return len(re.findall(r"\b(?:Int|Double|Float|String|Bool|UInt|Int64|Int32)\s*\(", text))
    return 0


def _is_import_line(line: str, lang: str) -> bool:
    s = line.strip()
    if s == "":
        return False
    if lang == "cpp":
        return s.startswith("#include ")
    if lang == "rs":
        return s.startswith("use ")
    if lang == "cs":
        return s.startswith("using ")
    if lang in {"js", "ts"}:
        return s.startswith("import ") or ("require(" in s and s.startswith("const "))
    if lang == "go":
        return s == "import (" or s.startswith("import ") or (s.startswith('"') and s.endswith('"'))
    if lang in {"java", "kotlin", "swift"}:
        return s.startswith("import ")
    return False


def _extract_import_aliases(lines: list[str], lang: str) -> list[str]:
    aliases: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not _is_import_line(line, lang):
            continue

        if lang == "cpp":
            continue
        if lang == "rs":
            m_alias = re.search(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", line)
            if m_alias is not None:
                aliases.append(m_alias.group(1))
                continue
            if "{" in line:
                continue
            m_leaf = re.search(r"use\s+.*::([A-Za-z_][A-Za-z0-9_]*)\s*;", line)
            if m_leaf is not None:
                aliases.append(m_leaf.group(1))
            continue
        if lang == "cs":
            m_alias = re.match(r"using\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if m_alias is not None:
                aliases.append(m_alias.group(1))
                continue
            m_ns = re.match(r"using\s+([A-Za-z0-9_.]+)\s*;", line)
            if m_ns is not None:
                leaf = m_ns.group(1).split(".")[-1]
                aliases.append(leaf)
            continue
        if lang in {"js", "ts"}:
            m_req_alias = re.match(r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*require\(", line)
            if m_req_alias is not None:
                aliases.append(m_req_alias.group(1))
            m_req_obj = re.match(r"const\s+\{([^}]*)\}\s*=\s*require\(", line)
            if m_req_obj is not None:
                parts = [p.strip() for p in m_req_obj.group(1).split(",")]
                for part in parts:
                    if part == "":
                        continue
                    if ":" in part:
                        alias = part.split(":", 1)[1].strip()
                        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
                            aliases.append(alias)
                    elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", part):
                        aliases.append(part)
            m_import_as = re.match(r"import\s+\*\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s+from", line)
            if m_import_as is not None:
                aliases.append(m_import_as.group(1))
            m_import_default = re.match(r"import\s+([A-Za-z_][A-Za-z0-9_]*)\s+from", line)
            if m_import_default is not None:
                aliases.append(m_import_default.group(1))
            m_import_obj = re.match(r"import\s+\{([^}]*)\}\s+from", line)
            if m_import_obj is not None:
                parts = [p.strip() for p in m_import_obj.group(1).split(",")]
                for part in parts:
                    if part == "":
                        continue
                    if " as " in part:
                        alias = part.split(" as ", 1)[1].strip()
                        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias):
                            aliases.append(alias)
                    elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", part):
                        aliases.append(part)
            continue
        if lang == "go":
            m_alias_path = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s+"([^"]+)"', line)
            if m_alias_path is not None:
                aliases.append(m_alias_path.group(1))
                continue
            m_path = re.match(r'"([^"]+)"', line)
            if m_path is not None:
                leaf = m_path.group(1).split("/")[-1]
                aliases.append(leaf)
            continue
        if lang in {"java", "kotlin", "swift"}:
            m_imp = re.match(r"import\s+([A-Za-z0-9_.]+)", line)
            if m_imp is not None:
                leaf = m_imp.group(1).split(".")[-1]
                aliases.append(leaf)
            continue

    uniq: list[str] = []
    seen: set[str] = set()
    for a in aliases:
        if a == "" or a in seen:
            continue
        seen.add(a)
        uniq.append(a)
    return uniq


def _unused_import_estimate(lines: list[str], lang: str) -> int:
    aliases = _extract_import_aliases(lines, lang)
    if len(aliases) == 0:
        return 0
    body_lines: list[str] = []
    for line in lines:
        if not _is_import_line(line, lang):
            body_lines.append(line)
    body = "\n".join(body_lines)
    unused = 0
    for a in aliases:
        if len(a) <= 1:
            continue
        if re.search(r"\b" + re.escape(a) + r"\b", body) is None:
            unused += 1
    return unused


def _measure_lang(cfg: LangConfig) -> Metrics:
    out = Metrics()
    d = ROOT / cfg.rel_dir
    files = sorted(d.glob("*" + cfg.ext))
    for path in files:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        out.files += 1
        out.lines += len(lines)
        out.mut_count += len(re.findall(r"\bmut\b", text))
        out.paren_count += text.count("((") + text.count("))")
        out.cast_count += _cast_count(text, cfg.name)
        out.clone_count += len(re.findall(r"\.clone\s*\(", text))
        out.import_count += sum(1 for ln in lines if _is_import_line(ln, cfg.name))
        out.unused_import_est += _unused_import_estimate(lines, cfg.name)
    return out


def _render_table(result: dict[str, Metrics]) -> str:
    order = [cfg.name for cfg in LANGS]
    lines: list[str] = []
    lines.append("| lang | files | lines | mut | paren | cast | clone | imports | unused_import_est |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for lang in order:
        m = result[lang]
        lines.append(
            "| "
            + lang
            + f" | {m.files} | {m.lines} | {m.mut_count} | {m.paren_count} | {m.cast_count} | {m.clone_count} | {m.import_count} | {m.unused_import_est} |"
        )
    return "\n".join(lines)


def _render_delta_table(result: dict[str, Metrics]) -> str:
    base = result["cpp"]
    base_mut = _rate(base.mut_count, base.lines)
    base_paren = _rate(base.paren_count, base.lines)
    base_cast = _rate(base.cast_count, base.lines)
    base_clone = _rate(base.clone_count, base.lines)
    base_unused = _rate(base.unused_import_est, base.lines)

    lines: list[str] = []
    lines.append("| lang | mutΔ/kLoC | parenΔ/kLoC | castΔ/kLoC | cloneΔ/kLoC | unused_importΔ/kLoC |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for cfg in LANGS:
        if cfg.name == "cpp":
            continue
        m = result[cfg.name]
        lines.append(
            "| "
            + cfg.name
            + f" | {_rate(m.mut_count, m.lines) - base_mut:.2f}"
            + f" | {_rate(m.paren_count, m.lines) - base_paren:.2f}"
            + f" | {_rate(m.cast_count, m.lines) - base_cast:.2f}"
            + f" | {_rate(m.clone_count, m.lines) - base_clone:.2f}"
            + f" | {_rate(m.unused_import_est, m.lines) - base_unused:.2f} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure sample code quality metrics")
    parser.add_argument(
        "--out",
        default="docs-ja/plans/p1-multilang-output-quality-baseline.md",
        help="write markdown report to this path",
    )
    args = parser.parse_args()

    result: dict[str, Metrics] = {}
    for cfg in LANGS:
        result[cfg.name] = _measure_lang(cfg)

    today = _dt.date.today().isoformat()
    report: list[str] = []
    report.append("# P1-MQ-01 Baseline")
    report.append("")
    report.append(f"計測日: {today}")
    report.append("")
    report.append("実行コマンド:")
    report.append("")
    report.append("```bash")
    report.append("python3 tools/measure_multilang_quality.py")
    report.append("```")
    report.append("")
    report.append("## 生カウント")
    report.append("")
    report.append(_render_table(result))
    report.append("")
    report.append("## `sample/cpp` 比較（差分 / kLoC）")
    report.append("")
    report.append(_render_delta_table(result))
    report.append("")
    report.append("## 備考")
    report.append("")
    report.append("- `unused_import_est` は簡易推定（import alias の単語出現有無）です。")
    report.append("- `cast` は言語ごとの簡易パターンで計数しています（厳密構文解析ではありません）。")
    report.append("- `paren` は `((` と `))` の出現回数です。")
    report.append("")

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report), encoding="utf-8")
    print(f"[OK] wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
