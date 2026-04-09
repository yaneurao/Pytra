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
- 2026-04-02: `docs/ja/spec/spec-east.md` に `Call.meta.copy_elision_safe_v1` を追加。v1 は `bytes(bytearray)` 専用で、backend は linker が付けた metadata がある場合だけ alias / borrow へ最適化してよい。
- 2026-04-02: linker に narrow/fail-closed な v1 解析を実装。現状は `return bytes(local_bytearray)` が同一 module 内で readonly `list[bytes]` フローにしか入らないケースだけ annotate する。
- 2026-04-02: Lua emitter/runtime に `copy_elision_safe_v1` 対応を実装。`03_julia_set` は無回帰 PASS。`07_game_of_life_loop` は改善したが `--cmd-timeout-sec 600` ではまだ timeout。
- 2026-04-10: linker の final linked rows に対しても `_annotate_copy_elision_safe_v1()` を再適用し、Lua emitter の `core.bytes_ctor` fast path が `copy_elision_safe_v1` を素通りしていた不具合を修正。これで `07_game_of_life_loop.render()` の `return bytes(frame)` は `__pytra_bytes_alias(frame)` に変わることを確認。
- 2026-04-10: readonly subscript owner も non-escape 判定に含め、`pytra.utils.gif._lzw_encode()` の `return bytes(out)` も `__pytra_bytes_alias(out)` へ切り替わることを確認。残る hot path は cross-module の `grayscale_palette()` と `f.write(bytes(out))`。
