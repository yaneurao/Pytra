<a href="../../en/todo/lua.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Lua backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02（Lua fixture 140/140、stdlib 16/16、sample は full count 未再計測）

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Lua emitter: `src/toolchain/emit/lua/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Lua runtime: `src/runtime/lua/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-LUA-TYPE-ID-CLEANUP: Lua runtime から __pytra_isinstance を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Lua は `type()` がネイティブにあるので `__pytra_isinstance` は不要。

1. [ ] [ID: P0-LUA-TYPEID-CLN-S1] `src/runtime/lua/built_in/py_runtime.lua` から `__pytra_isinstance` を削除する
2. [ ] [ID: P0-LUA-TYPEID-CLN-S2] fixture + sample parity に回帰がないことを確認する

### P1-LUA-EMITTER: Lua emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-lua-emitter.md](../plans/p1-lua-emitter.md)

1. [x] [ID: P1-LUA-EMITTER-S1] `src/toolchain2/emit/lua/` に Lua emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/lua/` と TS emitter を参考にする。Lua 固有（1-based index、nil、metatables 等）だけ override（2026-04-01）
2. [x] [ID: P1-LUA-EMITTER-S2] `src/runtime/lua/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義（2026-04-01）
3. [x] [ID: P1-LUA-EMITTER-S3] fixture 全件の Lua emit 成功を確認する（2026-04-01）— `_transpile_in_memory(..., target='lua')` で fixture 136/136 emit success
4. [x] [ID: P1-LUA-EMITTER-S4] Lua runtime を toolchain2 の emit 出力と整合させる（2026-04-01）— Path/json/sys/png/glob/deque/ArgumentParser、class 継承、list/bytearray/string method、linked `pytra_isinstance` を整合
5. [ ] [ID: P1-LUA-EMITTER-S5] fixture + sample の Lua run parity を通す（`lua5.4`）— 2026-04-02 現在 `fixture 140/140 pass`、`stdlib 16/16 pass`。pure-Python generated helper の load を emitter guide に沿って修正し、`pytra.utils.png/gif` を `dofile()` で接続。`03_julia_set` は `--cmd-timeout-sec 600` で PASS まで回復し、PNG helper 単体も byte-level 一致を確認。さらに Lua emitter に `dict in` 専用化、`len(str/list/tuple/bytearray)` fast path、truthiness/ifexp の軽量化、assign RHS subscript の checked access を追加し、追加 fixture を含む full fixture `140/140 pass` を再確認。残差は主に sample 実行時間で、確認済みの timeout は `07_game_of_life_loop` と `18_mini_language_interpreter`（ともに 600s timeout）。sample full の最新 pass 数は未再計測
6. [x] [ID: P1-LUA-EMITTER-S6] stdlib の Lua parity を通す（`--case-root stdlib`）（2026-04-01）— `runtime_parity_check_fast.py --targets lua --case-root stdlib` で `16/16 pass`

### P2-LUA-LINT-FIX: Lua emitter のハードコード違反を修正する

1. [x] [ID: P2-LUA-LINT-S1] `check_emitter_hardcode_lint.py` で Lua の違反が 0 件になることを確認する（2026-04-01）— 0 件

### P3-COPY-ELISION: EAST3 に copy elision メタデータを追加し Lua の bytes コピーを最適化する

文脈: [docs/ja/plans/p3-copy-elision-east-meta.md](../plans/p3-copy-elision-east-meta.md)

`bytes(bytearray)` のコピーが GIF sample の hot path。emitter 独自判断でのコピー省略はセマンティクス違反（差し戻し済み）。linker の解析結果を `copy_elision_safe_v1` として EAST3 meta に載せ、emitter はそのフラグを見てのみ省略する。

1. [x] [ID: P3-COPY-ELISION-S1] `copy_elision_safe_v1` スキーマを spec-east.md に定義する（2026-04-02）— `Call.meta.copy_elision_safe_v1` を canonical linker metadata として定義
2. [x] [ID: P3-COPY-ELISION-S2] linker の def-use / non-escape 解析で copy elision 判定を実装する（2026-04-02）— v1 は narrow/fail-closed。`return bytes(local_bytearray)` が readonly `list[bytes]` フローにしか流れない場合だけ annotate
3. [x] [ID: P3-COPY-ELISION-S3] Lua emitter で `copy_elision_safe_v1` を参照してコピー省略を実装する（2026-04-02）— `__pytra_bytes_alias()` を導入し、metadata がある `bytes(bytearray)` だけ alias 化
4. [ ] [ID: P3-COPY-ELISION-S4] `07_game_of_life_loop` の Lua parity PASS + 性能改善を確認する — `03_julia_set` は無回帰 PASS。`07_game_of_life_loop` は copy elision 後も `--cmd-timeout-sec 600` で timeout

### P20-LUA-SELFHOST: Lua emitter で toolchain2 を Lua に変換し実行できるようにする

1. [ ] [ID: P20-LUA-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-LUA-SELFHOST-S1] toolchain2 全 .py を Lua に emit し、実行できることを確認する
3. [ ] [ID: P20-LUA-SELFHOST-S2] selfhost 用 Lua golden を配置する
4. [ ] [ID: P20-LUA-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-LUA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang lua --emit-target lua --case-root sample` で sample parity PASS
