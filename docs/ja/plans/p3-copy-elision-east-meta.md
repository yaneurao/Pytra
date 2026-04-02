# P3-COPY-ELISION: EAST3 / linker に copy elision メタデータを追加する

最終更新: 2026-04-02

## 背景

Lua の GIF sample（`07_game_of_life_loop`）で `bytes(bytearray)` のコピーが hot path になっている。Lua 担当が `__pytra_bytes(table)` のコピーを省略して `return v` にする最適化を試みたが、これは Python の `bytes(bytearray)` がコピーを作るセマンティクスに違反する。

emitter が勝手にコピー省略すると、元の `bytearray` を後から変更した場合に `bytes` 側も変わってしまい、出力が壊れる。最適化は EAST / linker の情報に基づいてのみ合法。

## 必要な情報

コピー省略が安全な条件:
1. コピー元（`bytearray`）がコピー後に変更されない（non-mutate after copy）
2. コピー結果（`bytes`）が読み取り専用でしか使われない（`borrow_kind: readonly_ref`）

これらは single-module の `borrow_kind`（spec-east.md §5）だけでは判定できず、whole-program analysis が必要。

## 既存の枠組み

EAST3 / linker に関連する既存メタデータ:
- `borrow_kind`: `value | readonly_ref | mutable_ref`（spec-east.md §5）
- `meta.linked_program_v1.non_escape_summary`: linker 段の non-escape 解析
- `meta.linked_program_v1.container_ownership_hints_v1`: コンテナ所有権ヒント

これらを拡張して copy elision 判定を載せる。

## 方針

1. linker の non-escape / def-use 解析を拡張し、「コピー元がコピー後に mutate されない」を判定する
2. 判定結果を Call ノードの `meta.copy_elision_safe_v1` として付与する
3. emitter は `copy_elision_safe_v1` がある場合のみコピーを省略してよい
4. `copy_elision_safe_v1` がない場合はコピーを生成する（fail-closed）

## 対象

- `src/toolchain2/link/` — linker の解析拡張
- `docs/ja/spec/spec-east.md` — `copy_elision_safe_v1` のスキーマ定義
- `src/toolchain2/emit/lua/` — copy elision 対応（最初の適用先）
- 全 emitter — 将来的に同じメタデータを参照して最適化可能

## 非対象

- emitter 側の独自判断によるコピー省略（禁止。EAST メタデータが正本）
- `borrow_kind=move` の導入（将来拡張候補だが本タスクのスコープ外）

## サブタスク

1. [ ] [ID: P3-COPY-ELISION-S1] `bytes(bytearray)` のコピー省略が安全な条件を形式化し、spec-east.md に `copy_elision_safe_v1` スキーマを定義する
2. [ ] [ID: P3-COPY-ELISION-S2] linker の def-use / non-escape 解析で copy elision 判定を実装する
3. [ ] [ID: P3-COPY-ELISION-S3] Lua emitter で `copy_elision_safe_v1` を参照してコピー省略を実装する
4. [ ] [ID: P3-COPY-ELISION-S4] `07_game_of_life_loop` の Lua parity が PASS し、性能が改善されることを確認する

## 決定ログ

- 2026-04-02: Lua 担当が `__pytra_bytes` のコピー省略を emitter 独自判断で実施 → セマンティクス違反として差し戻し。EAST / linker にメタデータを載せる経路で起票。
