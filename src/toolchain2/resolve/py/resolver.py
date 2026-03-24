"""east1 → east2 resolver: 型解決 + 正規化 (Python 固有 → 言語非依存).

現時点の resolve 責務:
  1. east_stage を 1 → 2 に更新
  2. schema_version: 1 を付与
  3. meta.dispatch_mode: "native" を付与

将来の resolve 責務 (P0-RESOLVE-S2 以降):
  - import graph のトポロジカルソート
  - cross-module 型解決
  - Python 固有の構文正規化 (range → ForRange, int → int64 等)
  - cast 挿入

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path


@dataclass
class ResolveResult:
    """resolve の結果。"""
    east2_doc: dict[str, JsonVal]
    source_path: str


def resolve_east1_to_east2(east1_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    """単一モジュールの east1 → east2 変換。

    east1_doc は破壊的に変更される (コピーしない)。
    """
    # 1. east_stage を 2 に更新
    east1_doc["east_stage"] = 2

    # 2. schema_version を付与
    east1_doc["schema_version"] = 1

    # 3. meta.dispatch_mode を付与
    meta = east1_doc.get("meta")
    if isinstance(meta, dict):
        if "dispatch_mode" not in meta:
            meta["dispatch_mode"] = "native"

    return east1_doc


def resolve_file(input_path: Path) -> ResolveResult:
    """east1 ファイルを読み込んで east2 に変換する。"""
    text: str = input_path.read_text(encoding="utf-8")
    raw: JsonVal = json.loads(text).raw
    if not isinstance(raw, dict):
        raise ValueError("east1 document must be a JSON object: " + str(input_path))
    east2_doc: dict[str, JsonVal] = raw
    resolve_east1_to_east2(east2_doc)
    source_path_val = east2_doc.get("source_path")
    sp: str = str(source_path_val) if source_path_val is not None else ""
    return ResolveResult(east2_doc=east2_doc, source_path=sp)


def east2_output_path_from_east1(east1_path: Path) -> Path:
    """east1 のパスから east2 出力パスを導出する。

    a.py.east1 → a.east2 (.py を除去して .east2 に変更)
    """
    name: str = east1_path.name
    # .py.east1 → .east2 (.py を除去)
    if name.endswith(".py.east1"):
        base: str = name[: len(name) - len(".py.east1")]
        return east1_path.parent / (base + ".east2")
    # フォールバック: .east1 → .east2
    if name.endswith(".east1"):
        base2: str = name[: len(name) - len(".east1")]
        return east1_path.parent / (base2 + ".east2")
    # 拡張子不明: そのまま .east2 を付与
    return east1_path.parent / (name + ".east2")
