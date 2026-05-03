#!/usr/bin/env python3
"""Generate Top100 language coverage artifacts.

Outputs:
  docs/ja/progress/top100-language-coverage.md
  docs/en/progress/top100-language-coverage.md
  docs/ja/progress/top100-language-coverage.json

Usage:
  python3 tools/gen/gen_top100_language_coverage.py
  python3 tools/gen/gen_top100_language_coverage.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

JA_MD = ROOT / "docs" / "ja" / "progress" / "top100-language-coverage.md"
EN_MD = ROOT / "docs" / "en" / "progress" / "top100-language-coverage.md"
JSON_PATH = ROOT / "docs" / "ja" / "progress" / "top100-language-coverage.json"

SNAPSHOT = {
    "source": "TIOBE Index for April 2026",
    "url": "https://www.tiobe.com/tiobe-index/",
    "retrieved_on": "2026-04-30",
    "stored_at": "docs/ja/progress/top100-language-coverage.json",
}

TOP_50 = [
    "Python",
    "C",
    "C++",
    "Java",
    "C#",
    "JavaScript",
    "Visual Basic",
    "SQL",
    "R",
    "Delphi/Object Pascal",
    "Scratch",
    "Perl",
    "Fortran",
    "PHP",
    "Go",
    "Rust",
    "MATLAB",
    "Assembly language",
    "Swift",
    "Ada",
    "PL/SQL",
    "Prolog",
    "COBOL",
    "Kotlin",
    "SAS",
    "Classic Visual Basic",
    "Objective-C",
    "Dart",
    "Ruby",
    "Lua",
    "Lisp",
    "Julia",
    "ML",
    "TypeScript",
    "Haskell",
    "VBScript",
    "ABAP",
    "OCaml",
    "Zig",
    "Caml",
    "Erlang",
    "X++",
    "Scala",
    "Transact-SQL",
    "PowerShell",
    "GML",
    "LabVIEW",
    "Ladder Logic",
    "Solidity",
    "(Visual) FoxPro",
]

TIER_51_100 = [
    "ActionScript",
    "Algol",
    "Apex",
    "Applescript",
    "Awk",
    "Bash",
    "bc",
    "BCPL",
    "Bourne shell",
    "CFML",
    "CL (OS/400)",
    "Clojure",
    "CoffeeScript",
    "Curl",
    "D",
    "Elixir",
    "F#",
    "GAMS",
    "Groovy",
    "Icon",
    "Inform",
    "Io",
    "J",
    "J#",
    "JScript",
    "JScript.NET",
    "Logo",
    "LotusScript",
    "LPC",
    "Mojo",
    "MQL5",
    "NetLogo",
    "Nim",
    "OpenCL",
    "PL/I",
    "Pure Data",
    "Q",
    "REBOL",
    "Ring",
    "RPG",
    "RPL",
    "S",
    "Small Basic",
    "Smalltalk",
    "Tcl",
    "V",
    "Vala/Genie",
    "VHDL",
    "Wolfram",
    "Xojo",
]

BACKEND_LANGS = {
    "C++",
    "Java",
    "C#",
    "JavaScript",
    "PHP",
    "Go",
    "Rust",
    "Swift",
    "Kotlin",
    "Dart",
    "Ruby",
    "Lua",
    "Julia",
    "TypeScript",
    "Zig",
    "Scala",
    "PowerShell",
    "Nim",
}

HOST_LANGS = {"Python"}

INTEROP_LANGS = {
    "C",
    "SQL",
    "Bourne shell",
    "JScript",
    "MQL5",
    "S",
}

DEFER_LANGS = {
    "Scratch",
    "Assembly language",
    "GML",
    "LabVIEW",
    "Ladder Logic",
    "(Visual) FoxPro",
    "Algol",
    "bc",
    "BCPL",
    "CFML",
    "CL (OS/400)",
    "Curl",
    "GAMS",
    "Icon",
    "Inform",
    "Io",
    "J",
    "J#",
    "JScript.NET",
    "Logo",
    "LotusScript",
    "LPC",
    "NetLogo",
    "PL/I",
    "Pure Data",
    "Q",
    "REBOL",
    "Ring",
    "RPG",
    "RPL",
    "Small Basic",
    "Xojo",
}

STATUS_OVERRIDES = {
    "Python": ("reference parser/resolver/toolchain source", "selfhost matrix は full pass ではない", "selfhost rows を段階的に埋める"),
    "C": ("C ABI / C-family runtime adjacency", "native C backend は未定義", "C++ runtime との境界を棚卸しする"),
    "C++": ("primary backend; representative fixture/sample/stdlib PASS; sample 7/18", "full sample sweep 11 fail（artifact CRC / object 型漏れ / min・max・enumerate）", "C++ sample blockers を型推定と builtin fallback で縮退する"),
    "Dart": ("target registered; C++ emitter host 生成 PASS", "devcontainer に `dart` CLI が無い", "Dart CLI を隔離環境へ追加して compile/parity"),
    "Zig": ("target registered; C++ emitter host 生成 PASS", "devcontainer に `zig` CLI が無い", "Zig CLI を隔離環境へ追加して compile/parity"),
    "Go": ("target registered; Go selfhost fixture 161/161 and sample 18/18 PASS", "stdlib selfhost sweep は次段で拡張", "Go selfhost stdlib parity と broader regression を維持する"),
    "TypeScript": ("target registered; emitter-host PASS row あり", "full selfhost 未完", "TS host parity を拡張する"),
    "Swift": ("target registered", "Linux devcontainer では Swift 未導入", "optional Swift image/gate を検討する"),
    "PowerShell": ("target registered; devcontainer `pwsh` あり", "host parity は未完", "PowerShell host parity を再実行する"),
}

BACKEND_PLAN = {
    "Visual Basic": ("T1", "VB.NET を .NET backend family として扱い、Classic VB は別行で保留条件を持たせる"),
    "R": ("T1", "numeric/vector semantics を syntax smoke として固定し、Python numeric subset との距離を測る"),
    "Delphi/Object Pascal": ("T2", "Pascal family profile と Free Pascal toolchain smoke を先に確認する"),
    "Perl": ("T1", "scalar/list/hash context の制限 subset を定め、script backend 候補にする"),
    "Fortran": ("T2", "numeric/array subset と gfortran compile smoke を確認する"),
    "MATLAB": ("T3", "Octave 互換 subset を先に調査し、proprietary runtime 依存を避ける"),
    "Ada": ("T2", "GNAT availability と strong typing mapping を確認する"),
    "PL/SQL": ("T3", "SQL interop lane と接続し、DB runtime 前提を backend 非依存に分離する"),
    "Prolog": ("T3", "unification/control model が Pytra subset と合うか syntax 調査に留める"),
    "COBOL": ("T3", "data division と compile smoke の入手性を先に確認する"),
    "SAS": ("T3", "proprietary runtime 前提のため open substitute の有無を確認する"),
    "Classic Visual Basic": ("T3", "Visual Basic から分離し、legacy runtime 入手性を blocker として固定する"),
    "Objective-C": ("T2", "C/Swift interop と ObjC runtime 方針を比較する"),
    "Lisp": ("T2", "Common Lisp / Scheme を分離し、方言選定から始める"),
    "ML": ("T2", "OCaml/SML との重複を整理する"),
    "Haskell": ("T3", "lazy semantics を避ける strict subset 可否を調査する"),
    "VBScript": ("T3", "Windows Script Host 前提を syntax/defer 境界として確認する"),
    "ABAP": ("T3", "proprietary runtime 前提のため interop/defer 降格条件を定める"),
    "OCaml": ("T1", "OCaml profile 調査を ML family の代表として先行する"),
    "Caml": ("T3", "OCaml row へ統合できるか確認する"),
    "Erlang": ("T2", "BEAM lane と actor/runtime model を調査する"),
    "X++": ("T3", "proprietary runtime 前提を blocker として固定する"),
    "Transact-SQL": ("T3", "SQL interop lane と接続し、DB runtime 前提を分離する"),
    "Solidity": ("T2", "EVM/security semantics を通常 backend と分けて調査する"),
}

DEFER_CONDITIONS = {
    "Scratch": "visual/block DSL のため、text IR から block model へ変換する中間 DSL が必要",
    "Assembly language": "ISA 固有で一括 backend 不可。LLVM/WASM 等の低レベル lane へ分離後に再評価",
    "GML": "GameMaker runtime 前提。engine API interop plan ができるまで defer",
    "LabVIEW": "visual/dataflow DSL。model exchange format の調査が先",
    "Ladder Logic": "PLC/safety runtime 前提。対象 PLC と検証責任範囲の定義が先",
    "(Visual) FoxPro": "legacy/proprietary runtime の入手性が低く、preserve/defer 理由を固定",
    "Algol": "historical language で実用 toolchain 目的が薄い",
    "bc": "calculator DSL として narrow domain。通常 backend より helper/interop 扱い",
    "BCPL": "historical language で実用 toolchain 目的が薄い",
    "CFML": "server/runtime DSL。ColdFusion 互換 runtime 前提を分離",
    "CL (OS/400)": "IBM i platform-specific lane。通常 backend と別設計",
    "Curl": "niche/runtime 前提で toolchain 入手性が blocker",
    "GAMS": "optimization DSL。solver/runtime interop が先",
    "Icon": "niche language で toolchain 入手性が blocker",
    "Inform": "interactive fiction DSL。domain-specific transform 条件が先",
    "Io": "niche language で toolchain 入手性が blocker",
    "J": "array language で semantics 差分が大きく、APL family 調査が先",
    "J#": "obsolete .NET language。supported runtime 不明",
    "JScript.NET": "obsolete .NET language。supported runtime 不明",
    "Logo": "education DSL。text backend 優先度が低い",
    "LotusScript": "Domino runtime 前提の platform-specific lane",
    "LPC": "MUD/domain runtime 前提で通常 backend と別設計",
    "NetLogo": "agent-based DSL。domain-specific transform 条件が先",
    "PL/I": "legacy language で実用 toolchain 目的が薄い",
    "Pure Data": "visual/dataflow DSL。model exchange 条件が先",
    "Q": "kdb+ runtime 前提。proprietary/runtime-specific lane",
    "REBOL": "niche language で toolchain 入手性が blocker",
    "Ring": "niche language で toolchain 入手性が blocker",
    "RPG": "IBM i platform-specific lane",
    "RPL": "calculator/platform DSL。narrow runtime",
    "Small Basic": "education/runtime-specific lane。Visual Basic family との関係整理が先",
    "Xojo": "proprietary IDE/runtime。text backend 優先度が低い",
}

SYNTAX_NEXT_DEFAULT = "syntax smoke と最小 compile/run gate を調査する"
DEFER_NEXT_DEFAULT = "defer 理由と解除条件を固定する"
INTEROP_NEXT_DEFAULT = "external runtime / ABI interop plan を作る"


@dataclass(frozen=True)
class CoverageRow:
    rank: int | str
    language: str
    category: str
    current_status: str
    last_blocker: str
    next_action: str
    backend_plan_tier: str
    backend_plan: str
    defer_condition: str


def _category(language: str) -> str:
    if language in HOST_LANGS:
        return "host"
    if language in BACKEND_LANGS:
        return "backend"
    if language in INTEROP_LANGS:
        return "interop"
    if language in DEFER_LANGS:
        return "defer"
    return "syntax"


def _default_status(language: str, category: str) -> tuple[str, str, str]:
    if category == "backend":
        return ("target registered", "host/parity は未完", f"{language} host parity を進める")
    if category == "host":
        return ("host/toolchain lane", "full selfhost 未完", "selfhost matrix を埋める")
    if category == "interop":
        return ("interop lane", "native backend は未定義", INTEROP_NEXT_DEFAULT)
    if category == "defer":
        return ("non-standard backend lane", "通常 text backend ではない", DEFER_NEXT_DEFAULT)
    return ("backend candidate", "runtime / type / module semantics 未調査", SYNTAX_NEXT_DEFAULT)


def build_rows() -> list[CoverageRow]:
    rows: list[CoverageRow] = []
    for rank, language in enumerate(TOP_50, start=1):
        rows.append(_build_row(rank, language))
    for language in TIER_51_100:
        rows.append(_build_row("51-100", language))
    if len(rows) != 100:
        raise AssertionError(f"expected 100 rows, got {len(rows)}")
    return rows


def _build_row(rank: int | str, language: str) -> CoverageRow:
    category = _category(language)
    status, blocker, next_action = STATUS_OVERRIDES.get(language, _default_status(language, category))
    plan_tier = ""
    plan = ""
    if isinstance(rank, int) and rank <= 50 and category == "syntax":
        plan_tier, plan = BACKEND_PLAN.get(language, ("T3", SYNTAX_NEXT_DEFAULT))
    defer_condition = DEFER_CONDITIONS.get(language, "")
    return CoverageRow(
        rank=rank,
        language=language,
        category=category,
        current_status=status,
        last_blocker=blocker,
        next_action=next_action,
        backend_plan_tier=plan_tier,
        backend_plan=plan,
        defer_condition=defer_condition,
    )


def build_json_doc() -> dict[str, object]:
    rows = build_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.category] = counts.get(row.category, 0) + 1
    return {
        "schema_version": 1,
        "source_snapshot": SNAPSHOT,
        "category_counts": counts,
        "rows": [asdict(row) for row in rows],
    }


def _md_table(rows: list[CoverageRow]) -> list[str]:
    lines = [
        "| rank | language | category | current status | last blocker | next action |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.rank} | {row.language} | {row.category} | "
            f"{row.current_status} | {row.last_blocker} | {row.next_action} |"
        )
    return lines


def _backend_plan_table(rows: list[CoverageRow]) -> list[str]:
    candidates = [row for row in rows if row.backend_plan_tier]
    lines = [
        "| tier | language | plan | blocker |",
        "|---|---|---|---|",
    ]
    for row in candidates:
        lines.append(f"| {row.backend_plan_tier} | {row.language} | {row.backend_plan} | {row.last_blocker} |")
    return lines


def _defer_table(rows: list[CoverageRow]) -> list[str]:
    candidates = [row for row in rows if row.category == "defer"]
    lines = [
        "| language | defer condition | unblock condition |",
        "|---|---|---|",
    ]
    for row in candidates:
        condition = row.defer_condition or "通常 text backend として扱う前に別設計が必要"
        lines.append(f"| {row.language} | {condition} | {row.next_action} |")
    return lines


def render_ja_markdown() -> str:
    rows = build_rows()
    doc = build_json_doc()
    counts = doc["category_counts"]
    lines = [
        '<a href="../../en/progress/top100-language-coverage.md">',
        '  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">',
        "</a>",
        "",
        "# Top100 言語 coverage matrix",
        "",
        "最終更新: 2026-05-03",
        "",
        "## Source snapshot",
        "",
        f"- 出典: {SNAPSHOT['source']}",
        f"- URL: {SNAPSHOT['url']}",
        f"- 取得日: {SNAPSHOT['retrieved_on']}",
        f"- machine-readable catalog: `{SNAPSHOT['stored_at']}`",
        "- 位置付け: 外部の人気指標スナップショット。Pytra では優先度付けに使い、技術的適性は別途 `backend` / `host` / `interop` / `syntax` / `defer` で判断する。",
        "",
        "## 今回の実測",
        "",
        "- 仮想環境: Docker Desktop CLI (`/Applications/Docker.app/Contents/Resources/bin/docker`) で `.devcontainer/Dockerfile` を直接 build。`devcontainer` 常設 CLI は PATH 上に無かったため、グローバル導入せず Dockerfile 直接 run に fallback。",
        "- Docker: `docker version` と `docker run --rm hello-world` は PASS。初回 build は `docker-credential-desktop` が PATH に無く失敗し、Docker Desktop 同梱 bin を PATH に追加して再実行 PASS。",
        "- toolchain: `.devcontainer/scripts/verify-toolchain.sh` は PASS。Python 3.12 / pytest / C/C++ / Java / .NET / PowerShell / Ruby / Lua / PHP / Go / Rust を確認。Swift は optional 未導入。`dart` / `zig` CLI は未導入。",
        "- runtime east: `PYTHONPATH=src python3 tools/gen/regenerate_runtime_east.py` は `runtime-east total: 32 ok, 0 failed`。",
        "- unit/top100 generator: `python3 -m pytest -q tools/unittest/tooling/test_gen_top100_language_coverage.py tools/unittest/toolchain2/test_tuple_unpack_emitter_hosts.py` は 10 tests PASS。`python3 tools/gen/gen_top100_language_coverage.py --check` と `python3 tools/check/check_tools_ledger.py` も PASS。",
        "- emitter-host: `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target dart ...` は PASS（25 files）。`--target zig ...` も PASS（emitted 30 files、検証ディレクトリ内 file count 39）。native Dart/Zig CLI は devcontainer 未導入のため compile/parity は blocker として残す。",
        "- fixture/sample/stdlib/selfhost: C++ plain builtin fallback を runtime helper 経路へ戻し、Docker 直接 run で `fixture core/add`、`sample 17_monte_carlo_pi`、`stdlib math_extended` の C++ parity が PASS。sample full sweep は 18件中 7 PASS / 11 FAIL。Go selfhost は Docker 隔離環境で fixture 161/161 と sample 18/18 PASS。残 blocker は C++ sample の artifact CRC / object 型漏れ / `min`・`max`・`enumerate` fallback と、Go selfhost stdlib sweep の拡張。",
        "",
        "## 分類ルール",
        "",
        "- `backend`: Pytra target として emit でき、progress matrix へ接続する。",
        "- `host`: Pytra toolchain / emitter の host として扱う。",
        "- `interop`: 既存 runtime / ABI / query engine との接続対象にする。",
        "- `syntax`: backend 化判断に必要な構文・型・module 調査を先に行う。",
        "- `defer`: Scratch / Ladder Logic / LabVIEW など、通常の text backend として扱う前に別設計が必要なため、解除条件を待つ。",
        "",
        "## 集計",
        "",
        f"- backend: {counts.get('backend', 0)}",
        f"- host: {counts.get('host', 0)}",
        f"- interop: {counts.get('interop', 0)}",
        f"- syntax: {counts.get('syntax', 0)}",
        f"- defer: {counts.get('defer', 0)}",
        "",
        "## Matrix",
        "",
        *_md_table(rows),
        "",
        "## Top50 未対応候補 backend plan",
        "",
        "T1 は次回以降の syntax smoke / profile 調査を優先する候補、T2 は toolchain 入手性や runtime 形状を先に見る候補、T3 は proprietary / DSL / semantics 差分が大きく通常 backend 化の前に境界判断が必要な候補です。",
        "",
        *_backend_plan_table(rows),
        "",
        "## defer 条件",
        "",
        *_defer_table(rows),
        "",
        "## Docker/devcontainer 標準ゲート",
        "",
        "Top100 coverage を更新する run は、次の順で Docker/devcontainer gate を通す。Docker が使えない場合は coverage を完了扱いにせず、exact blocker と再開条件だけを残す。",
        "",
        "1. `docker version` と `docker run --rm hello-world` で Engine と container start を確認する。",
        "2. `devcontainer` 常設 CLI があれば `.devcontainer/` を起動する。無い場合は Docker Desktop 同梱 bin を PATH に足して `.devcontainer/Dockerfile` を直接 build/run する。",
        "3. コンテナ内で `.devcontainer/scripts/verify-toolchain.sh`、`tools/gen/regenerate_runtime_east.py`、`tools/gen/gen_top100_language_coverage.py --check` を実行する。",
        "4. 代表 fixture / sample / stdlib / emitter-host / selfhost の実測コマンドを残し、未導入 runtime は blocker として matrix に戻す。",
        "",
        "## 次アクション",
        "",
        "1. Dart / Zig CLI を devcontainer に追加するか、別 image として分離し、今回 PASS した host 生成物を compile/parity まで進める。",
        "2. Go selfhost stdlib sweep を追加し、fixture/sample に続く runtime coverage を固定する。",
        "3. C++ sample の残 blocker（artifact CRC、object 型漏れ、`min` / `max` / `enumerate` fallback）を縮退し、selfhost cpp row を PASS 側へ寄せる。",
        "4. T1 backend plan（Visual Basic / R / Perl / OCaml）から syntax smoke を作り、top100 matrix の `syntax` を実測つきに更新する。",
        "",
    ]
    return "\n".join(lines)


def render_en_markdown() -> str:
    rows = build_rows()
    doc = build_json_doc()
    counts = doc["category_counts"]
    lines = [
        '<a href="../../ja/progress/top100-language-coverage.md">',
        '  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">',
        "</a>",
        "",
        "# Top100 Language Coverage Matrix",
        "",
        "Last updated: 2026-05-03",
        "",
        "## Source Snapshot",
        "",
        f"- Source: {SNAPSHOT['source']}",
        f"- URL: {SNAPSHOT['url']}",
        f"- Retrieved on: {SNAPSHOT['retrieved_on']}",
        f"- Machine-readable catalog: `{SNAPSHOT['stored_at']}`",
        "- Role: external popularity snapshot for prioritization. Technical fit is tracked separately as `backend` / `host` / `interop` / `syntax` / `defer`.",
        "",
        "## Verification Gate",
        "",
        "- Environment: Docker Desktop CLI with direct `.devcontainer/Dockerfile` build/run. The permanent `devcontainer` CLI was not on PATH, so the run uses direct Docker without global installs.",
        "- Docker: `docker version` and `docker run --rm hello-world` must pass before coverage updates are accepted.",
        "- Toolchain: `.devcontainer/scripts/verify-toolchain.sh` checks Python 3.12, pytest, C/C++, Java, .NET, PowerShell, Ruby, Lua, PHP, Go, and Rust. Swift is optional; Dart/Zig CLIs remain blockers until added.",
        "- Coverage update gate: `python3 tools/gen/gen_top100_language_coverage.py --check` runs inside the container after generation.",
        "- Representative parity: C++ fixture `core/add`, sample `17_monte_carlo_pi`, and stdlib `math_extended` pass after routing plain builtin calls back through runtime helpers. The refreshed C++ full sample sweep is 7/18 PASS. Go selfhost now passes fixture 161/161 and sample 18/18 in the Docker-isolated environment; the next Go step is extending the selfhost stdlib sweep.",
        "",
        "## Category Counts",
        "",
        f"- backend: {counts.get('backend', 0)}",
        f"- host: {counts.get('host', 0)}",
        f"- interop: {counts.get('interop', 0)}",
        f"- syntax: {counts.get('syntax', 0)}",
        f"- defer: {counts.get('defer', 0)}",
        "",
        "## Matrix",
        "",
        *_md_table(rows),
        "",
        "## Top50 Backend Candidate Plan",
        "",
        *_backend_plan_table(rows),
        "",
        "## Defer Conditions",
        "",
        *_defer_table(rows),
        "",
    ]
    return "\n".join(lines)


def _expected_outputs() -> dict[Path, str]:
    json_doc = build_json_doc()
    return {
        JA_MD: render_ja_markdown(),
        EN_MD: render_en_markdown(),
        JSON_PATH: json.dumps(json_doc, ensure_ascii=False, indent=2) + "\n",
    }


def write_outputs() -> None:
    for path, content in _expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> int:
    failed = False
    for path, expected in _expected_outputs().items():
        if not path.exists():
            print(f"[FAIL] missing generated file: {path.relative_to(ROOT)}", file=sys.stderr)
            failed = True
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"[FAIL] stale generated file: {path.relative_to(ROOT)}", file=sys.stderr)
            failed = True
    if failed:
        print("run: python3 tools/gen/gen_top100_language_coverage.py", file=sys.stderr)
        return 1
    print("[OK] top100 language coverage artifacts are current")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Top100 language coverage artifacts")
    parser.add_argument("--check", action="store_true", help="check generated files without writing")
    parser.add_argument("--dump-json", action="store_true", help="print generated JSON to stdout")
    args = parser.parse_args(argv)
    if args.dump_json:
        print(json.dumps(build_json_doc(), ensure_ascii=False, indent=2))
        return 0
    if args.check:
        return check_outputs()
    write_outputs()
    for path in _expected_outputs():
        print(f"[OK] wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
