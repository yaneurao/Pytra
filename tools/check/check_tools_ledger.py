"""
tools/ 台帳突合チェック。
tools/README.md に記載のないスクリプトが tools/check/ / tools/gen/ / tools/run/ に
存在すれば FAIL とする。tools/ 直下の .py ファイル（自分自身を除く）も FAIL 対象。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
LEDGER = TOOLS / "README.md"

MANAGED_DIRS = ["check", "gen", "run"]


def _ledger_entries() -> set[str]:
    """README.md 内の | `filename.py` | ... | 行からファイル名を抽出する。"""
    text = LEDGER.read_text(encoding="utf-8")
    entries: set[str] = set()
    for m in re.finditer(r"`([A-Za-z0-9_.]+\.py)`", text):
        entries.add(m.group(1))
    return entries


def main() -> int:
    if not LEDGER.exists():
        print("FAIL: tools/README.md が存在しません。台帳を作成してください。")
        return 1

    ledger = _ledger_entries()
    errors: list[str] = []

    # tools/ 直下の .py ファイルは禁止（このスクリプト自身は check/ にある）
    for f in TOOLS.glob("*.py"):
        errors.append(f"FAIL: tools/{f.name} は tools/ 直下に置けません。check/gen/run/ のいずれかへ移動してください。")

    # tools/check/ / tools/gen/ / tools/run/ のファイルが台帳に載っているか確認
    for sub in MANAGED_DIRS:
        subdir = TOOLS / sub
        if not subdir.exists():
            continue
        for f in sorted(subdir.glob("*.py")):
            if f.name not in ledger:
                errors.append(f"FAIL: tools/{sub}/{f.name} が tools/README.md に記載されていません。台帳を更新してください。")

    if errors:
        for e in errors:
            print(e)
        return 1

    total = sum(len(list((TOOLS / sub).glob("*.py"))) for sub in MANAGED_DIRS if (TOOLS / sub).exists())
    print(f"OK: tools/ 台帳突合チェック PASS ({total} スクリプト確認)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
